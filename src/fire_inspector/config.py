"""讀取 .env 設定。錯誤訊息只寫「哪個項目有問題」,不印出任何設定的內容(token 是機密)。"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


class ConfigError(Exception):
    """.env 設定有缺漏或格式不對。訊息寫給使用者看,所以用白話中文。"""


@dataclass(frozen=True)
class Config:
    discord_token: str
    channel_id: int
    claude_model: str
    data_dir: Path
    semester_start: date


def load_config(environ: Mapping[str, str]) -> Config:
    problems: list[str] = []

    def value(name: str) -> str | None:
        text = (environ.get(name) or "").strip()
        if not text:
            problems.append(f"缺少 {name}(請在 .env 裡填寫)")
            return None
        return text

    token = value("DISCORD_TOKEN")
    channel_text = value("CHANNEL_ID")
    model = value("CLAUDE_MODEL")
    data_dir_text = value("DATA_DIR")
    semester_text = value("SEMESTER_START")

    channel_id = None
    if channel_text is not None:
        if channel_text.isdigit():
            channel_id = int(channel_text)
        else:
            problems.append("CHANNEL_ID 必須是一串數字(頻道的 ID)")

    semester_start = None
    if semester_text is not None:
        try:
            semester_start = date.fromisoformat(semester_text)
        except ValueError:
            problems.append("SEMESTER_START 的格式不對,請寫成 年-月-日,例如 2026-09-01")

    if problems:
        raise ConfigError(".env 設定有問題:\n- " + "\n- ".join(problems))

    return Config(
        discord_token=token,
        channel_id=channel_id,
        claude_model=model,
        data_dir=Path(data_dir_text),
        semester_start=semester_start,
    )


def load_config_from_env() -> Config:
    """讀目前資料夾(或上層)的 .env,再檢查所有設定。"""
    load_dotenv(find_dotenv(usecwd=True))
    return load_config(os.environ)
