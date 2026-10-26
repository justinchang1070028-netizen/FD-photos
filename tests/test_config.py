from datetime import date
from pathlib import Path

import pytest

from fire_inspector.config import ConfigError, load_config

VALID = {
    "DISCORD_TOKEN": "SECRET-TOKEN-xyz",
    "CHANNEL_ID": "123456789012345678",
    "CLAUDE_MODEL": "claude-sonnet-5-5",
    "DATA_DIR": r"C:\Users\user\FD-photos-data",
    "SEMESTER_START": "2026-09-01",
}


def test_valid_settings_are_loaded_with_the_right_types():
    config = load_config(VALID)
    assert config.discord_token == "SECRET-TOKEN-xyz"
    assert config.channel_id == 123456789012345678
    assert config.claude_model == "claude-sonnet-5-5"
    assert config.data_dir == Path(r"C:\Users\user\FD-photos-data")
    assert config.semester_start == date(2026, 9, 1)


def test_surrounding_spaces_are_ignored():
    config = load_config({**VALID, "CLAUDE_MODEL": "  claude-sonnet-5-5  "})
    assert config.claude_model == "claude-sonnet-5-5"


@pytest.mark.parametrize("name", list(VALID))
def test_each_missing_setting_is_named_in_the_error(name):
    environ = {k: v for k, v in VALID.items() if k != name}
    with pytest.raises(ConfigError) as error:
        load_config(environ)
    assert name in str(error.value)


def test_blank_value_counts_as_missing():
    with pytest.raises(ConfigError) as error:
        load_config({**VALID, "CLAUDE_MODEL": "   "})
    assert "CLAUDE_MODEL" in str(error.value)


def test_all_problems_are_reported_together():
    with pytest.raises(ConfigError) as error:
        load_config({"DISCORD_TOKEN": "x"})
    message = str(error.value)
    for name in ("CHANNEL_ID", "CLAUDE_MODEL", "DATA_DIR", "SEMESTER_START"):
        assert name in message


def test_channel_id_must_be_a_number():
    with pytest.raises(ConfigError) as error:
        load_config({**VALID, "CHANNEL_ID": "abc"})
    assert "CHANNEL_ID" in str(error.value)


def test_semester_start_must_be_a_real_date_in_year_month_day_form():
    with pytest.raises(ConfigError) as error:
        load_config({**VALID, "SEMESTER_START": "2026/9/1"})
    assert "SEMESTER_START" in str(error.value)
    assert "2026-09-01" in str(error.value)  # 提示正確寫法


def test_the_token_never_appears_in_an_error_message():
    with pytest.raises(ConfigError) as error:
        load_config({**VALID, "CHANNEL_ID": "abc"})
    assert "SECRET-TOKEN-xyz" not in str(error.value)
