"""Discord 這一層:收訊息、排隊、一次處理一張、回覆。判斷與記帳都交給其他模組。"""

import asyncio
import logging
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
from zoneinfo import ZoneInfo

import discord

from fire_inspector.attachments import select_attachment, verify_image
from fire_inspector.config import Config
from fire_inspector.counting import already_counted_on, count_passing_days
from fire_inspector.models import Record
from fire_inspector.recent_ids import RecentIds
from fire_inspector.replies import (
    FAILURE_REPLY,
    QUERY_FAILURE_REPLY,
    fit_to_discord,
    is_my_record_command,
    my_record_reply,
    queue_notice,
    record_cells,
    render_reply,
)
from fire_inspector.reviewer import ReviewError, review_photo
from fire_inspector.sanitize import build_photo_filename
from fire_inspector.storage import RecordStore
from fire_inspector.verdict import compute_overall

log = logging.getLogger(__name__)

TAIPEI = ZoneInfo("Asia/Taipei")
MAX_PENDING_PER_USER = 3
FLUSH_INTERVAL_SECONDS = 30
INVALID_IMAGE_REPLY = "⚠️ 這個檔案不是有效的 jpg / png / webp 圖片,請重傳。"
TOO_MANY_PENDING_REPLY = f"你已經有 {MAX_PENDING_PER_USER} 張在排隊,請等處理完再傳。"


@dataclass
class Job:
    message: discord.Message
    attachment: discord.Attachment
    extra_images: int
    placeholder: discord.Message | None


class FireInspectorBot(discord.Client):
    def __init__(self, config: Config, store: RecordStore):
        intents = discord.Intents.default()
        intents.message_content = True  # 要在開發者後台也打開,否則收不到附件
        super().__init__(intents=intents)
        self.config = config
        self.store = store
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self.pending_by_user: Counter[int] = Counter()
        self.seen_message_ids = RecentIds()  # 超過上限只丟最舊的,不會整個清空
        self.processing = False
        self._worker_task: asyncio.Task | None = None
        # 審查流程和 /我的紀錄 都會讀寫 Excel,用一把鎖讓它們輪流來
        self._store_lock = asyncio.Lock()

    async def setup_hook(self) -> None:
        self._worker_task = asyncio.create_task(self._worker())

    async def close(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
        await super().close()

    async def on_ready(self) -> None:
        log.info("已登入為 %s,正在監聽頻道 %s", self.user, self.config.channel_id)

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id != self.config.channel_id or message.author.bot:
            return

        # 查詢指令:直接讀 Excel 回答,完全不呼叫 claude -p(就算同時附了照片也一樣)
        if is_my_record_command(message.content):
            await self._answer_my_record(message)
            return

        selected = select_attachment(message.attachments)
        if selected is None:
            return
        attachment, extra_images = selected

        if message.id in self.seen_message_ids:
            return
        self.seen_message_ids.add(message.id)

        user_id = message.author.id
        if self.pending_by_user[user_id] >= MAX_PENDING_PER_USER:
            await self._reply(message, TOO_MANY_PENDING_REPLY)
            return

        ahead = self.queue.qsize() + (1 if self.processing else 0)
        placeholder = await self._reply(message, queue_notice(ahead), notify=False)
        self.pending_by_user[user_id] += 1
        await self.queue.put(Job(message, attachment, extra_images, placeholder))

    async def _answer_my_record(self, message: discord.Message) -> None:
        try:
            records = await self._store(self.store.all_records)
        except Exception:
            log.exception("查詢紀錄失敗")
            await self._reply(message, QUERY_FAILURE_REPLY)
            return
        total = count_passing_days(records, message.author.id, self.config.semester_start)
        await self._reply(message, my_record_reply(total))

    async def _store(self, function, *args):
        """所有 Excel / 照片存取都經過這裡:一次只讓一個人用,而且不卡住 Discord 的連線。"""
        async with self._store_lock:
            return await asyncio.to_thread(function, *args)

    # ---- 一次處理一張 ----

    async def _worker(self) -> None:
        while True:
            try:
                job = await asyncio.wait_for(self.queue.get(), FLUSH_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                await self._flush_pending()  # 閒置時順便把暫存區補進 Excel
                continue

            self.processing = True
            try:
                await self._handle(job)
            except Exception:  # 單張照片出事,不能讓整個 bot 停掉
                log.exception("處理訊息 %s 時發生未預期的錯誤", job.message.id)
                await self._finish(job, FAILURE_REPLY)
            finally:
                self.processing = False
                self.pending_by_user[job.message.author.id] -= 1
            await self._flush_pending()

    async def _handle(self, job: Job) -> None:
        message = job.message
        data = await job.attachment.read()
        try:
            extension = verify_image(data)
        except ValueError as error:
            log.warning("訊息 %s 的附件不是有效圖片:%s", message.id, error)
            await self._finish(job, INVALID_IMAGE_REPLY)
            return

        try:
            review = await review_photo(
                data,
                extension,
                model=self.config.claude_model,
                work_root=self.config.data_dir / "work",
            )
        except ReviewError as error:
            log.error("訊息 %s 審查失敗,不建檔、不計次數:%s", message.id, error)
            await self._finish(job, FAILURE_REPLY)
            return

        overall = compute_overall(review)
        taken_at = message.created_at.astimezone(TAIPEI).replace(tzinfo=None)
        user_id = message.author.id
        nickname = message.author.display_name

        filename = build_photo_filename(taken_at, nickname, message.author.name, user_id, extension)
        photo_path = await self._store(self.store.save_photo, filename, data)

        records = await self._store(self.store.all_records)
        counted_before = already_counted_on(records, user_id, taken_at.date())
        clothing, shoes, hair, other = record_cells(review, overall)
        draft = Record(
            taken_at=taken_at,
            uploader=nickname,
            user_id=user_id,
            clothing=clothing,
            shoes=shoes,
            hair=hair,
            other=other,
            overall=overall,
            cumulative=0,
            photo_path=photo_path,
        )
        cumulative = count_passing_days([*records, draft], user_id, self.config.semester_start)
        await self._store(self.store.add, replace(draft, cumulative=cumulative))

        text = render_reply(
            review,
            overall,
            cumulative,
            counted_today_before=counted_before,
            extra_images=job.extra_images,
        )
        await self._finish(job, fit_to_discord(text))
        log.info("訊息 %s 完成:%s,累計 %d", message.id, overall, cumulative)

    async def _flush_pending(self) -> None:
        try:
            await self._store(self.store.flush_pending)
        except Exception:
            log.exception("把暫存區補進 Excel 時出錯")

    # ---- 回覆 ----

    async def _finish(self, job: Job, text: str) -> None:
        """刪掉「處理中」,再用新的回覆送出結果(這樣上傳者會收到通知)。"""
        if job.placeholder is not None:
            try:
                await job.placeholder.delete()
            except discord.HTTPException:
                pass
        await self._reply(job.message, text)

    async def _reply(self, message: discord.Message, text: str, *, notify: bool = True):
        # 只允許提及上傳者本人;claude 回覆裡的 @everyone、身分組都不會生效
        if notify:
            mentions = discord.AllowedMentions(
                everyone=False, roles=False, users=[message.author], replied_user=True
            )
        else:
            mentions = discord.AllowedMentions.none()
        try:
            return await message.reply(text, mention_author=notify, allowed_mentions=mentions)
        except discord.NotFound:  # 原訊息被刪了
            return await message.channel.send(text, allowed_mentions=mentions)
        except discord.HTTPException:
            log.exception("送出回覆失敗")
            return None
