"""綜合判定。由程式自己算,不採用模型說的結果。"""

from fire_inspector.schema import ITEM_NAMES, ReviewResult


def compute_overall(review: ReviewResult) -> str:
    """回傳 合格 / 不合格 / 無法判定 / 無效照片。

    優先順序:無效照片 > 任一項 fail > 模型說無法判定 > 任一項 not_visible > 合格。
    warn(材質看不出、建議換隱形眼鏡)不影響結果。
    """
    if not review.valid_photo:
        return "無效照片"

    statuses = [getattr(review, name).status for name in ITEM_NAMES]
    if "fail" in statuses:
        return "不合格"
    if review.overall == "無法判定":
        return "無法判定"
    if "not_visible" in statuses:
        return "不合格"
    return "合格"
