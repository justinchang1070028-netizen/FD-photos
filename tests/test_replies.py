import pytest

from fire_inspector.replies import (
    FAILURE_REPLY,
    queue_notice,
    record_cells,
    render_reply,
)
from tests.helpers import parsed

NOT_VALID = dict(
    valid_photo=False,
    invalid_description="一張貓的照片",
    clothing=None, shoes=None, hair=None,
    accessories=None, mask=None, glasses=None,
)


def reply(review, overall, cumulative=7, **kwargs):
    kwargs.setdefault("counted_today_before", False)
    kwargs.setdefault("extra_images", 0)
    return render_reply(review, overall, cumulative, **kwargs)


# --- 完整回覆 ---


def test_qualified_reply_lists_six_items_verdict_and_cumulative_count():
    text = reply(parsed(), "合格", cumulative=7)
    for number, label in enumerate(
        ["衣服與褲子", "鞋子", "頭髮", "首飾配件", "口罩", "眼鏡/隱眼"], start=1
    ):
        assert f"{number}. {label}:✅" in text
    assert "最終判定:✅ 合格" in text
    assert "本學期累計合格:7 次" in text


def test_each_status_gets_its_own_mark():
    review = parsed(
        clothing={"status": "warn", "comment": "看不出成分。"},
        shoes={"status": "fail", "comment": "涼鞋。"},
        glasses={"status": "warn", "comment": "建議換隱形。"},
    )
    text = reply(review, "不合格")
    assert "1. 衣服與褲子:⚠️ 看不出成分。" in text
    assert "2. 鞋子:❌ 涼鞋。" in text
    assert "6. 眼鏡/隱眼:⚠️ 建議換隱形。" in text


def test_unqualified_verdict_names_the_failed_items():
    review = parsed(
        shoes={"status": "fail", "comment": "涼鞋。"},
        hair={"status": "fail", "comment": "披頭散髮。"},
    )
    assert "最終判定:❌ 不合格(鞋子、頭髮)" in reply(review, "不合格")


def test_warnings_are_not_listed_as_reasons_for_failing():
    review = parsed(
        clothing={"status": "warn", "comment": "看不出成分。"},
        hair={"status": "fail", "comment": "沒夾瀏海。"},
    )
    text = reply(review, "不合格")
    assert "不合格(頭髮)" in text
    assert "衣服與褲子)" not in text


def test_not_visible_item_asks_for_a_full_body_retake():
    review = parsed(shoes={"status": "not_visible", "comment": "腳沒入鏡。"})
    text = reply(review, "不合格")
    assert "2. 鞋子:⚠️ 看不到:腳沒入鏡。" in text
    assert "不合格(鞋子)" in text
    assert "重傳" in text


def test_cannot_judge_asks_for_a_better_photo():
    text = reply(parsed(overall="無法判定"), "無法判定", cumulative=3)
    assert "最終判定:⚠️ 無法判定" in text
    assert "重拍" in text
    assert "本學期累計合格:3 次" in text


def test_invalid_photo_says_what_it_is_and_still_shows_the_count():
    text = reply(parsed(**NOT_VALID), "無效照片", cumulative=4)
    assert "你傳的不是服裝檢查照,是一張貓的照片" in text
    assert "最終判定:無效照片" in text
    assert "本學期累計合格:4 次" in text
    assert "1. 衣服與褲子" not in text


def test_multiple_people_note_is_added():
    text = reply(parsed(multiple_people=True), "合格")
    assert "照片中有多人,只審查主要人物" in text


def test_extra_images_note_is_added():
    text = reply(parsed(), "合格", extra_images=2)
    assert "一次請只傳一張" in text


def test_already_counted_today_note_only_for_a_qualified_repeat():
    assert "今天已計過,次數不變" in reply(parsed(), "合格", counted_today_before=True)
    assert "今天已計過" not in reply(parsed(), "合格", counted_today_before=False)
    assert "今天已計過" not in reply(
        parsed(hair={"status": "fail", "comment": "x"}), "不合格", counted_today_before=True
    )


@pytest.mark.parametrize(
    ("review", "overall"),
    [
        (parsed(), "合格"),
        (parsed(hair={"status": "fail", "comment": "x"}), "不合格"),
        (parsed(overall="無法判定"), "無法判定"),
        (parsed(**NOT_VALID), "無效照片"),
    ],
)
def test_every_kind_of_reply_includes_the_cumulative_count(review, overall):
    assert "本學期累計合格:12 次" in reply(review, overall, cumulative=12)


# --- 其他固定文字 ---


def test_queue_notice_mentions_how_many_are_ahead():
    assert queue_notice(0) == "⏳ 處理中⋯⋯"
    assert "前面還有 3 張" in queue_notice(3)


def test_failure_reply_asks_to_resend_without_blaming_the_member():
    assert "沒審查成功" in FAILURE_REPLY
    assert "重傳" in FAILURE_REPLY


# --- Excel 儲存格內容 ---


def test_record_cells_have_mark_plus_comment_and_merged_last_cell():
    review = parsed(
        clothing={"status": "warn", "comment": "材質無法判斷。"},
        accessories={"status": "fail", "comment": "戴手錶。"},
        glasses={"status": "warn", "comment": "建議換隱形。"},
    )
    clothing, shoes, hair, other = record_cells(review, "不合格")
    assert clothing == "⚠️ 材質無法判斷。"
    assert shoes == "✅ 布鞋。"
    assert hair == "✅ 馬尾。"
    assert other == "首飾 ❌ 戴手錶。;口罩 ✅;眼鏡 ⚠️ 建議換隱形。"


def test_record_cells_for_invalid_photo_are_all_marked_invalid():
    assert record_cells(parsed(**NOT_VALID), "無效照片") == ("無效照片",) * 4


# --- Discord 單則訊息上限 2000 字 ---


def test_short_text_is_left_alone():
    from fire_inspector.replies import fit_to_discord

    assert fit_to_discord("很短的回覆") == "很短的回覆"


def test_over_long_text_is_cut_but_keeps_the_verdict_and_the_count():
    from fire_inspector.replies import fit_to_discord

    text = "\n".join(["火安服裝審查結果:"] + ["字" * 600] * 5 + ["最終判定:✅ 合格", "本學期累計合格:7 次"])
    fitted = fit_to_discord(text)
    assert len(fitted) <= 2000
    assert fitted.endswith("最終判定:✅ 合格\n本學期累計合格:7 次")


def test_over_long_text_keeps_a_verdict_that_is_followed_by_an_extra_note():
    from fire_inspector.replies import fit_to_discord

    tail = ["最終判定:❌ 不合格(鞋子)", "有項目拍不到,請重傳一張完整的全身照。", "本學期累計合格:7 次"]
    text = "\n".join(["火安服裝審查結果:"] + ["字" * 600] * 5 + tail)
    fitted = fit_to_discord(text)
    assert len(fitted) <= 2000
    assert fitted.endswith("\n".join(tail))


# --- /我的紀錄 指令 ---


def test_command_is_found_anywhere_in_the_text():
    from fire_inspector.replies import is_my_record_command

    assert is_my_record_command("/我的紀錄")
    assert is_my_record_command("請問一下 /我的紀錄 謝謝")


@pytest.mark.parametrize("text", ["我的紀錄", "/我的記錄", "/records", "", None])
def test_other_text_is_not_the_command(text):
    from fire_inspector.replies import is_my_record_command

    assert not is_my_record_command(text)


def test_my_record_reply_states_the_semester_total():
    from fire_inspector.replies import my_record_reply

    assert my_record_reply(7) == "你的本學期累計合格總次數為 7 次"
    assert my_record_reply(0) == "你的本學期累計合格總次數為 0 次"
