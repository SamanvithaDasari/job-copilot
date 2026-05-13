"""Entry point. Phase 1.4: Telegram bot receiving messages."""
import logging
from src.config import config
from src.telegram_bot import build_application

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    # Validate config
    missing = config.validate()
    if missing:
        print("❌ Configuration issues:")
        for item in missing:
            print(f"  - {item}")
        return

    logger.info("Starting Job Copilot…")
    logger.info(f"Notifying chat IDs: {config.TELEGRAM_CHAT_IDS}")

    # Build and start the bot.
    # run_polling() blocks here — bot runs until you hit Ctrl+C.
    app = build_application()
    logger.info("Bot is running. Send it a message in Telegram.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()