from datetime import datetime

import pytest

from fire_inspector.sanitize import (
    build_photo_filename,
    ensure_inside,
    safe_cell_text,
    unique_path,
)

TAKEN_AT = datetime(2026, 10, 27, 19, 30, 45)


# --- 防護 3:暱稱轉檔名 ---


def test_filename_has_timestamp_nickname_and_extension():
    name = build_photo_filename(TAKEN_AT, "小明", "ming1234", 42, ".jpg")
    assert name == "20261027-193045_小明.jpg"


@pytest.mark.parametrize(
    ("nickname", "expected_part"),
    [
        ("..\\..\\x", "x"),
        ("a/b", "ab"),
        ("C:evil", "Cevil"),
        ('a*b?c"d<e>f|g', "abcdefg"),
        ("小明🔥火舞", "小明火舞"),
    ],
)
def test_path_characters_are_removed_from_nickname(nickname, expected_part):
    name = build_photo_filename(TAKEN_AT, nickname, "user", 42, ".png")
    assert name == f"20261027-193045_{expected_part}.png"


def test_nickname_is_cut_to_8_characters():
    name = build_photo_filename(TAKEN_AT, "一二三四五六七八九十", "user", 42, ".jpg")
    assert name == "20261027-193045_一二三四五六七八.jpg"


def test_emoji_only_nickname_falls_back_to_username():
    name = build_photo_filename(TAKEN_AT, "🔥🔥🔥", "ming1234", 42, ".jpg")
    assert name == "20261027-193045_ming1234.jpg"


def test_nickname_and_username_both_empty_fall_back_to_user_id():
    name = build_photo_filename(TAKEN_AT, "🔥", "///", 42, ".jpg")
    assert name == "20261027-193045_42.jpg"


def test_windows_reserved_name_still_gives_a_legal_filename():
    name = build_photo_filename(TAKEN_AT, "CON", "user", 42, ".jpg")
    assert name == "20261027-193045_CON.jpg"


def test_unique_path_adds_suffix_when_name_is_taken(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"1")
    assert unique_path(tmp_path, "a.jpg") == tmp_path / "a-2.jpg"
    (tmp_path / "a-2.jpg").write_bytes(b"2")
    assert unique_path(tmp_path, "a.jpg") == tmp_path / "a-3.jpg"


def test_unique_path_keeps_name_when_free(tmp_path):
    assert unique_path(tmp_path, "a.jpg") == tmp_path / "a.jpg"


def test_ensure_inside_accepts_path_in_folder(tmp_path):
    ensure_inside(tmp_path, tmp_path / "a.jpg")


def test_ensure_inside_rejects_path_that_escapes_folder(tmp_path):
    with pytest.raises(ValueError):
        ensure_inside(tmp_path / "photos", tmp_path / "photos" / ".." / "records.xlsx")


# --- 防護 4:Excel 儲存格文字 ---


@pytest.mark.parametrize(
    "text",
    ["=1+1", "+1", "-1", "@SUM(1)", '=HYPERLINK("http://example.com","x")', "\t=1+1"],
)
def test_formula_like_text_gets_a_leading_apostrophe(text):
    assert safe_cell_text(text).startswith("'")


def test_normal_text_is_unchanged():
    assert safe_cell_text("❌ 戴手錶;口罩 ✅") == "❌ 戴手錶;口罩 ✅"


def test_control_characters_are_removed():
    assert safe_cell_text("a\x00b\x07c") == "abc"


def test_newlines_become_spaces():
    assert safe_cell_text("第一行\n第二行\r\n第三行") == "第一行 第二行 第三行"


def test_long_text_is_cut_to_300_characters():
    result = safe_cell_text("字" * 500)
    assert len(result) == 300
    assert result.endswith("…")


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_or_blank_text_is_not_treated_as_formula(text):
    assert not safe_cell_text(text).startswith("'")
