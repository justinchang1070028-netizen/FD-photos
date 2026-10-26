import json

import pytest

from fire_inspector.schema import ReviewParseError, parse_review
from fire_inspector.verdict import compute_overall


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


# --- compute_overall ---


def test_all_pass_is_qualified():
    assert compute_overall(parsed()) == "合格"


def test_warn_on_clothing_and_glasses_does_not_fail():
    review = parsed(
        clothing={"status": "warn", "comment": "看不出成分。"},
        glasses={"status": "warn", "comment": "建議換隱形眼鏡。"},
    )
    assert compute_overall(review) == "合格"


def test_one_fail_is_unqualified():
    review = parsed(hair={"status": "fail", "comment": "瀏海沒夾。"})
    assert compute_overall(review) == "不合格"


def test_not_visible_item_is_unqualified():
    review = parsed(shoes={"status": "not_visible", "comment": "腳沒入鏡。"})
    assert compute_overall(review) == "不合格"


def test_invalid_photo_is_invalid_even_if_model_says_qualified():
    review = parsed(
        valid_photo=False,
        invalid_description="一張貓的照片",
        clothing=None, shoes=None, hair=None,
        accessories=None, mask=None, glasses=None,
        overall="合格",
    )
    assert compute_overall(review) == "無效照片"


def test_program_overrides_model_that_says_qualified_despite_a_fail():
    review = parsed(
        accessories={"status": "fail", "comment": "戴手錶。"},
        overall="合格",
    )
    assert compute_overall(review) == "不合格"


def test_model_cannot_judge_and_no_fail_is_cannot_judge():
    assert compute_overall(parsed(overall="無法判定")) == "無法判定"


def test_a_definite_fail_beats_model_cannot_judge():
    review = parsed(
        shoes={"status": "fail", "comment": "涼鞋。"},
        overall="無法判定",
    )
    assert compute_overall(review) == "不合格"


# --- parse_review ---


def test_parse_accepts_json_wrapped_in_prose():
    text = "好的,以下是結果:\n" + json.dumps(make_review(), ensure_ascii=False) + "\n希望有幫助"
    assert parse_review(text).valid_photo is True


def test_parse_rejects_non_json():
    with pytest.raises(ReviewParseError):
        parse_review("抱歉,我看不到照片")


def test_parse_rejects_missing_item_when_photo_is_valid():
    data = make_review()
    del data["shoes"]
    with pytest.raises(ReviewParseError):
        parse_review(json.dumps(data, ensure_ascii=False))


def test_parse_rejects_unknown_status():
    data = make_review(shoes={"status": "maybe", "comment": "不確定。"})
    with pytest.raises(ReviewParseError):
        parse_review(json.dumps(data, ensure_ascii=False))


def test_glasses_can_never_fail():
    data = make_review(glasses={"status": "fail", "comment": "戴眼鏡。"})
    with pytest.raises(ReviewParseError):
        parse_review(json.dumps(data, ensure_ascii=False))


def test_long_comment_is_truncated_to_300_chars():
    data = make_review(hair={"status": "fail", "comment": "長" * 500})
    review = parse_review(json.dumps(data, ensure_ascii=False))
    assert len(review.hair.comment) == 300
    assert review.hair.comment.endswith("…")
