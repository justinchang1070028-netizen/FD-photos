"""啟動入口:uv run fire-inspector"""

import logging
import sys

import discord

from fire_inspector.bot import FireInspectorBot
from fire_inspector.config import ConfigError, load_config_from_env
from fire_inspector.storage import RecordStore


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    try:
        config = load_config_from_env()
    except ConfigError as error:
        sys.exit(str(error))

    config.data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.data_dir / "bot.log", encoding="utf-8"),
        ],
    )

    store = RecordStore(config.data_dir)
    try:
        store.all_records()
    except PermissionError:
        # 讀不到就沒有資料可以算累計次數,硬跑會算錯
        sys.exit("讀不到 records.xlsx。請先把 Excel 關掉,再重新啟動。")

    bot = FireInspectorBot(config, store)
    try:
        bot.run(config.discord_token, log_handler=None)
    except discord.LoginFailure:
        sys.exit("登入 Discord 失敗:DISCORD_TOKEN 不正確。請到開發者後台重設 token 後更新 .env。")
    except discord.PrivilegedIntentsRequired:
        sys.exit("請到 Discord 開發者後台 → Bot,打開 Message Content Intent 並按 Save Changes。")


if __name__ == "__main__":
    main()
