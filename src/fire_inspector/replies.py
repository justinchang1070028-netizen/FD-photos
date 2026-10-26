"""回覆社員的文字,以及寫進 Excel 的判定儲存格內容。"""

from fire_inspector.schema import ITEM_NAMES, ReviewResult

FAILURE_REPLY = "⚠️ 這張照片這次沒審查成功,請重傳一次。"
QUERY_FAILURE_REPLY = "⚠️ 暫時查不到你的紀錄,請稍後再試。"
MY_RECORD_COMMAND = "/我的紀錄"


def is_my_record_command(text: str | None) -> bool:
    return bool(text) and MY_RECORD_COMMAND in text


def my_record_reply(cumulative: int) -> str:
    return f"你的本學期累計合格總次數為 {cumulative} 次"

_LABELS = {
    "clothing": "衣服與褲子",
    "shoes": "鞋子",
    "hair": "頭髮",
    "accessories": "首飾配件",
    "mask": "口罩",
    "glasses": "眼鏡/隱眼",
}
_MARKS = {"pass": "✅", "fail": "❌", "warn": "⚠️", "not_visible": "⚠️"}


def queue_notice(ahead: int) -> str:
    if ahead <= 0:
        return "⏳ 處理中⋯⋯"
    return f"⏳ 處理中⋯⋯(前面還有 {ahead} 張)"


def _item_text(item) -> str:
    if item.status == "not_visible":
        return f"{_MARKS['not_visible']} 看不到:{item.comment}"
    return f"{_MARKS[item.status]} {item.comment}"


def _verdict_lines(review: ReviewResult, overall: str) -> list[str]:
    if overall == "合格":
        return ["最終判定:✅ 合格"]
    if overall == "不合格":
        items = [getattr(review, name) for name in ITEM_NAMES]
        failed = [
            _LABELS[name]
            for name, item in zip(ITEM_NAMES, items)
            if item.status in ("fail", "not_visible")
        ]
        lines = [f"最終判定:❌ 不合格({'、'.join(failed)})"]
        if any(item.status == "not_visible" for item in items):
            lines.append("有項目拍不到,請重傳一張完整的全身照。")
        return lines
    if overall == "無法判定":
        return ["最終判定:⚠️ 無法判定", "照片太暗或太糊,請在光線好的地方重拍後重傳。"]
    return ["最終判定:無效照片"]


def render_reply(
    review: ReviewResult,
    overall: str,
    cumulative: int,
    *,
    counted_today_before: bool,
    extra_images: int,
) -> str:
    lines: list[str] = []
    if overall == "無效照片":
        description = review.invalid_description.strip().rstrip("。.")
        lines += [f"你傳的不是服裝檢查照,是{description}。", "請傳一張練舞前的全身自拍。", ""]
    else:
        lines += ["火安服裝審查結果:", ""]
        for number, name in enumerate(ITEM_NAMES, start=1):
            lines.append(f"{number}. {_LABELS[name]}:{_item_text(getattr(review, name))}")
        lines.append("")
        if review.multiple_people:
            lines.append("照片中有多人,只審查主要人物。")

    if extra_images > 0:
        lines.append("一次請只傳一張,這次只審查第一張。")

    lines += _verdict_lines(review, overall)

    count_line = f"本學期累計合格:{cumulative} 次"
    if overall == "合格" and counted_today_before:
        count_line += "(今天已計過,次數不變)"
    lines.append(count_line)
    return "\n".join(lines)


def record_cells(review: ReviewResult, overall: str) -> tuple[str, str, str, str]:
    """Excel 的四個判定欄:衣服/褲子、鞋子、頭髮、首飾+口罩+眼鏡合併。"""
    if overall == "無效照片":
        return ("無效照片",) * 4

    def merged(label: str, item) -> str:
        return f"{label} ✅" if item.status == "pass" else f"{label} {_item_text(item)}"

    other = ";".join(
        [
            merged("首飾", review.accessories),
            merged("口罩", review.mask),
            merged("眼鏡", review.glasses),
        ]
    )
    return (
        _item_text(review.clothing),
        _item_text(review.shoes),
        _item_text(review.hair),
        other,
    )


DISCORD_MESSAGE_LIMIT = 2000
_NEWLINE = chr(10)


def fit_to_discord(text: str, limit: int = DISCORD_MESSAGE_LIMIT) -> str:
    """超過單則訊息上限時,截掉中間的反饋,但一定保留「最終判定」起到結尾的所有行。"""
    if len(text) <= limit:
        return text
    lines = text.split(_NEWLINE)
    verdict_at = next(
        (i for i, line in enumerate(lines) if line.startswith("最終判定:")), len(lines) - 2
    )
    tail = _NEWLINE.join(lines[verdict_at:])
    head = _NEWLINE.join(lines[:verdict_at])
    room = limit - len(tail) - 2
    return head[:room] + "…" + _NEWLINE + tail
