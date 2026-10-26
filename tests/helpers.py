"""測試共用的範例資料。"""

import json

from fire_inspector.schema import parse_review


def make_review(**overrides):
    review = {
        "valid_photo": True,
        "invalid_description": "",
        "multiple_people": False,
        "clothing": {"status": "pass", "comment": "棉質。"},
        "shoes": {"status": "pass", "comment": "布鞋。"},
        "hair": {"status": "pass", "comment": "馬尾。"},
        "accessories": {"status": "pass", "comment": "沒有首飾。"},
        "mask": {"status": "pass", "comment": "沒戴口罩。"},
        "glasses": {"status": "pass", "comment": "沒戴眼鏡。"},
        "overall": "合格",
    }
    review.update(overrides)
    return review


def parsed(**overrides):
    return parse_review(json.dumps(make_review(**overrides), ensure_ascii=False))
