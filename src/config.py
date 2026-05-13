"""Loads environment variables and provides typed config access."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root is one level up from src/
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(ROOT_DIR / ".env")


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    # Designed as a list from day one (even though it's 1 user now) —
    # makes it trivial to add your friend later as a co-recipient.
    TELEGRAM_CHAT_IDS: list[str] = [
        cid.strip()
        for cid in os.getenv("TELEGRAM_CHAT_IDS", "").split(",")
        if cid.strip()
    ]

    # Google Sheets
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    SERVICE_ACCOUNT_PATH: Path = ROOT_DIR / os.getenv(
        "SERVICE_ACCOUNT_PATH", "credentials/service-account.json"
    )

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # App settings
    FIT_SCORE_THRESHOLD: int = int(os.getenv("FIT_SCORE_THRESHOLD", "70"))
    RESUME_PATH: Path = ROOT_DIR / os.getenv("RESUME_PATH", "resume.txt")

    @classmethod
    def resume_text(cls) -> str:
        """Read the resume file. Called via profile() abstraction later."""
        return cls.RESUME_PATH.read_text(encoding="utf-8")

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of missing/invalid config items. Empty list = all good."""
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_IDS:
            missing.append("TELEGRAM_CHAT_IDS")
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not cls.SERVICE_ACCOUNT_PATH.exists():
            missing.append(f"service-account.json not found at {cls.SERVICE_ACCOUNT_PATH}")
        if not cls.RESUME_PATH.exists():
            missing.append(f"resume.txt not found at {cls.RESUME_PATH}")
        # GOOGLE_SHEET_ID intentionally not validated yet (we set it in step 1.3)
        return missing


config = Config()


# --- profile() abstraction ---
# Right now there's only one profile (you). When/if we ever go multi-user,
# this is the single function we change — every consumer reads through here.
def profile():
    """Return the current user's profile. Currently always returns the default."""
    return config