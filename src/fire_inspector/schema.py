"""claude -p 回傳的 JSON 格式定義與解析。"""

import json
from typing import Literal

from pydantic import BaseModel, ValidationError, field_validator, model_validator

MAX_COMMENT_LENGTH = 300

ITEM_NAMES = ("clothing", "shoes", "hair", "accessories", "mask", "glasses")


class ReviewParseError(Exception):
    """claude 的回答無法解析成合法的審查結果。"""


class _Item(BaseModel):
    comment: str = ""

    @field_validator("comment")
    @classmethod
    def _truncate(cls, value: str) -> str:
        if len(value) > MAX_COMMENT_LENGTH:
            return value[: MAX_COMMENT_LENGTH - 1] + "…"
        return value


class Item(_Item):
    status: Literal["pass", "fail", "warn", "not_visible"]


class GlassesItem(_Item):
    # 眼鏡只是建議,永遠不會是 fail 或 not_visible
    status: Literal["pass", "warn"]


class ReviewResult(BaseModel):
    valid_photo: bool
    invalid_description: str = ""
    multiple_people: bool = False
    clothing: Item | None = None
    shoes: Item | None = None
    hair: Item | None = None
    accessories: Item | None = None
    mask: Item | None = None
    glasses: GlassesItem | None = None
    overall: Literal["合格", "不合格", "無法判定"]

    @model_validator(mode="after")
    def _items_required_for_valid_photo(self) -> "ReviewResult":
        if self.valid_photo:
            missing = [name for name in ITEM_NAMES if getattr(self, name) is None]
            if missing:
                raise ValueError(f"有效照片缺少項目:{', '.join(missing)}")
        return self


def parse_review(text: str) -> ReviewResult:
    """從 claude 的回答取出 JSON 並驗證。回答前後多了說明文字也能處理。"""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ReviewParseError("回答中找不到 JSON")
    try:
        return ReviewResult.model_validate(json.loads(text[start : end + 1]))
    except (ValueError, ValidationError) as error:
        raise ReviewParseError(str(error)) from error
