"""Entry point. Phase 1: just verifies the setup is working."""
from src.config import config


def main():
    print("Job Copilot starting up…")
    print()

    missing = config.validate()
    if missing:
        print("❌ Configuration issues:")
        for item in missing:
            print(f"  - {item}")
        print()
        print("Fix these in .env (or check files exist), then re-run.")
        return

    print("✅ Config looks good!")
    print(f"  Telegram bot: ...{config.TELEGRAM_BOT_TOKEN[-6:]} (last 6 chars)")
    print(f"  Chat IDs: {config.TELEGRAM_CHAT_IDS}")
    print(f"  Service account: {config.SERVICE_ACCOUNT_PATH.name}")
    print(f"  Resume: {len(config.resume_text())} characters loaded")
    print(f"  Gemini key: …{config.GEMINI_API_KEY[-6:]}")
    print()
    print("Ready for Step 1.3 (Google Sheet wiring).")


if __name__ == "__main__":
    main()