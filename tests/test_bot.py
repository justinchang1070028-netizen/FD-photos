import asyncio
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from fire_inspector import bot as bot_module
from fire_inspector.bot import FireInspectorBot
from fire_inspector.config import Config
from fire_inspector.models import Record
from fire_inspector.storage import RecordStore

CHANNEL_ID = 111


class FakeMessage:
    """Discord 訊息的替身:記下機器人對它做了哪些回覆。"""

    def __init__(self, content, *, author_id=42, channel_id=CHANNEL_ID, bot=False,
                 attachments=(), message_id=1):
        self.id = message_id
        self.content = content
        self.attachments = list(attachments)
        self.channel = SimpleNamespace(id=channel_id)
        self.author = SimpleNamespace(id=author_id, bot=bot, name="ming", display_name="小明")
        self.replies = []

    async def reply(self, text, **kwargs):
        self.replies.append(text)
        return SimpleNamespace(delete=self._noop)

    @staticmethod
    async def _noop():
        return None


def image_attachment():
    return SimpleNamespace(content_type="image/jpeg", size=1000, filename="a.jpg")


def passing_record(day, user_id=42):
    return Record(
        taken_at=datetime(2026, 10, day, 18, 0), uploader="小明", user_id=user_id,
        clothing="✅", shoes="✅", hair="✅", other="✅", overall="合格",
        cumulative=0, photo_path="photos/x.jpg",
    )


@pytest.fixture
def make_bot(tmp_path, monkeypatch):
    def forbid_claude(*args, **kwargs):
        raise AssertionError("這個情況不應該呼叫 claude -p")

    monkeypatch.setattr(bot_module, "review_photo", forbid_claude)

    def build(records=()):
        store = RecordStore(tmp_path)
        for record in records:
            store.add(record)
        config = Config(
            discord_token="never-used", channel_id=CHANNEL_ID, claude_model="m",
            data_dir=Path(tmp_path), semester_start=date(2026, 9, 1),
        )
        return FireInspectorBot(config, store), store

    return build


def send(bot, message):
    asyncio.run(bot.on_message(message))


# --- /我的紀錄 ---


def test_my_record_command_replies_with_the_members_own_total(make_bot):
    bot, _ = make_bot([passing_record(1), passing_record(2), passing_record(3),
                       passing_record(1, user_id=99)])
    message = FakeMessage("/我的紀錄")
    send(bot, message)
    assert message.replies == ["你的本學期累計合格總次數為 3 次"]


def test_my_record_command_works_inside_a_longer_sentence(make_bot):
    bot, _ = make_bot([passing_record(1)])
    message = FakeMessage("嗨 /我的紀錄 麻煩了")
    send(bot, message)
    assert message.replies == ["你的本學期累計合格總次數為 1 次"]


def test_my_record_command_for_a_member_without_records_says_zero(make_bot):
    bot, _ = make_bot()
    message = FakeMessage("/我的紀錄")
    send(bot, message)
    assert message.replies == ["你的本學期累計合格總次數為 0 次"]


def test_my_record_command_never_calls_claude_or_queues_anything(make_bot):
    bot, _ = make_bot([passing_record(1)])
    message = FakeMessage("/我的紀錄", attachments=[image_attachment()])
    send(bot, message)  # 就算同時附了照片,也只查詢(review_photo 被換成會報錯的替身)
    assert bot.queue.qsize() == 0
    assert message.replies == ["你的本學期累計合格總次數為 1 次"]


def test_my_record_command_reads_the_current_excel_so_manual_edits_count(make_bot):
    bot, store = make_bot([passing_record(1), passing_record(2)])
    first = FakeMessage("/我的紀錄", message_id=1)
    send(bot, first)
    store.add(passing_record(5))
    second = FakeMessage("/我的紀錄", message_id=2)
    send(bot, second)
    assert first.replies == ["你的本學期累計合格總次數為 2 次"]
    assert second.replies == ["你的本學期累計合格總次數為 3 次"]


def test_my_record_command_when_excel_cannot_be_read_gives_a_friendly_message(make_bot, monkeypatch):
    bot, store = make_bot()

    def unreadable():
        raise PermissionError("Excel 開著")

    monkeypatch.setattr(store, "all_records", unreadable)
    message = FakeMessage("/我的紀錄")
    send(bot, message)
    assert len(message.replies) == 1
    assert "暫時查不到" in message.replies[0]


def test_command_is_ignored_in_other_channels_and_from_bots(make_bot):
    bot, _ = make_bot([passing_record(1)])
    elsewhere = FakeMessage("/我的紀錄", channel_id=999)
    from_bot = FakeMessage("/我的紀錄", bot=True)
    send(bot, elsewhere)
    send(bot, from_bot)
    assert elsewhere.replies == [] and from_bot.replies == []


def test_ordinary_chat_is_still_ignored(make_bot):
    bot, _ = make_bot()
    message = FakeMessage("今天晚上練舞嗎?")
    send(bot, message)
    assert message.replies == [] and bot.queue.qsize() == 0


# --- 照片進佇列、重複訊息 ---


def test_a_photo_gets_a_placeholder_and_is_queued_once(make_bot):
    bot, _ = make_bot()
    message = FakeMessage("", attachments=[image_attachment()], message_id=7)
    send(bot, message)
    send(bot, message)  # 同一則訊息重複送來,不可以處理兩次
    assert bot.queue.qsize() == 1
    assert message.replies == ["⏳ 處理中⋯⋯"]
