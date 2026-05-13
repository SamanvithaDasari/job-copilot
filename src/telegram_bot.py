"""Telegram bot: receives messages, sends notifications."""
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from src.config import config

logger = logging.getLogger(__name__)


def extract_urls(text: str) -> list[str]:
    """Pull all URLs out of a message."""
    pattern = r"https?://[^\s<>\"']+"
    return re.findall(pattern, text)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def handle_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Job Copilot is running!\n\n"
        "Send me a job URL and I'll add it to your sheet.\n\n"
        "Commands:\n"
        "/status — see what's in your queue\n"
        "/help — show this message"
    )


async def handle_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use:\n\n"
        "• Paste any job URL → I'll track it\n"
        "• /status → see recent jobs\n"
        "• More features coming soon!"
    )


async def handle_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Show a quick count of jobs by status."""
    from src.sheets import get_all_jobs
    try:
        jobs = get_all_jobs()
        if not jobs:
            await update.message.reply_text("No jobs tracked yet. Paste a URL to start!")
            return

        # Count by status
        counts: dict[str, int] = {}
        for job in jobs:
            s = job.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1

        lines = [f"📋 *Job tracker status:*\n"]
        for status, count in sorted(counts.items()):
            emoji = {
                "new": "🆕",
                "applied": "✅",
                "rejected": "❌",
                "archived": "🗃️",
            }.get(status, "•")
            lines.append(f"{emoji} {status}: {count}")
        lines.append(f"\n*Total: {len(jobs)} jobs tracked*")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.exception("Status command failed")
        await update.message.reply_text(f"Error reading sheet: {e}")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle any non-command text message."""
    text = update.message.text or ""
    urls = extract_urls(text)

    if not urls:
        await update.message.reply_text(
            "I didn't spot a URL in that message.\n"
            "Paste a job link starting with https:// and I'll track it."
        )
        return

    # Process each URL found in the message
    from src.sheets import url_exists, add_job

    results = []
    for url in urls:
        if url_exists(url):
            results.append(f"⚠️ Already tracked: {url[:60]}…")
            continue

        # For now: add with placeholder data.
        # Phase 1.4 just proves the pipeline works.
        # Phase 2 will scrape the JD and score it properly.
        job_id = add_job(
            source="telegram_manual",
            company="Pending",
            title="Pending — will be parsed next cycle",
            location="Unknown",
            url=url,
            status="new",
            notes="Added via Telegram. Pending parse.",
        )
        results.append(f"✅ Added to sheet: `{job_id}`\n{url[:60]}…")

    reply = "\n\n".join(results)
    await update.message.reply_text(reply, parse_mode="Markdown")


# ── Outbound notifications ────────────────────────────────────────────────────

async def _send_async(text: str, url: str | None = None):
    """Send a message to all configured chat IDs."""
    from telegram import Bot
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    for chat_id in config.TELEGRAM_CHAT_IDS:
        kwargs: dict = {"parse_mode": "Markdown"}
        if url:
            keyboard = [[InlineKeyboardButton("Open job", url=url)]]
            kwargs["reply_markup"] = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)


def send_notification(text: str, url: str | None = None):
    """Synchronous wrapper — call this from the orchestrator."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_async(text, url))
    except RuntimeError:
        asyncio.run(_send_async(text, url))


# ── App builder ───────────────────────────────────────────────────────────────

def build_application() -> Application:
    """Build and return the configured bot application."""
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app