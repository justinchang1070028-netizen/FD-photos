"""把別人送進來的文字清乾淨:暱稱 → 檔名(防護 3)、文字 → Excel 儲存格(防護 4)。"""

import re
from datetime import datetime
from pathlib import Path

NICKNAME_MAX_LENGTH = 8
CELL_MAX_LENGTH = 300


# ===== 防護 3 開始:暱稱轉檔名前清掉會讓路徑亂跑的字 =====
def _filename_part(text: str) -> str:
    # 只留文字、數字、底線。/ \ .. : * ? " < > | 與 emoji 全部因此被去掉
    return re.sub(r"[^\w]", "", text)[:NICKNAME_MAX_LENGTH]


def build_photo_filename(
    taken_at: datetime, nickname: str, username: str, user_id: int, extension: str
) -> str:
    """日期時間 + 暱稱簡稱。暱稱清完是空的就退回帳號名稱,再退回帳號 ID。"""
    part = _filename_part(nickname) or _filename_part(username) or str(user_id)
    return f"{taken_at:%Y%m%d-%H%M%S}_{part}{extension}"


def ensure_inside(folder: Path, path: Path) -> None:
    """最終路徑一定要落在 folder 之內,否則拒絕。"""
    if not path.resolve().is_relative_to(folder.resolve()):
        raise ValueError(f"路徑跑到資料夾外面了:{path}")
# ===== 防護 3 結束 =====


def unique_path(folder: Path, filename: str) -> Path:
    """同名檔案已存在時,在副檔名前加 -2、-3……,絕不覆蓋。"""
    candidate = folder / filename
    stem, suffix = candidate.stem, candidate.suffix
    counter = 2
    while candidate.exists():
        candidate = folder / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


# ===== 防護 4 開始:寫進 Excel 的文字以 = + - @ 開頭時轉成純文字 =====
_ILLEGAL_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_FORMULA_STARTS = ("=", "+", "-", "@")


def safe_cell_text(text: str) -> str:
    text = _ILLEGAL_XML_CHARS.sub("", text)
    text = re.sub(r"[\r\n]+", " ", text)
    if text.startswith("\t") or text.lstrip().startswith(_FORMULA_STARTS):
        text = "'" + text
    if len(text) > CELL_MAX_LENGTH:
        text = text[: CELL_MAX_LENGTH - 1] + "…"
    return text
# ===== 防護 4 結束 =====
