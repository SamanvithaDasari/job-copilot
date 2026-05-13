"""Google Sheets read/write. The source of truth for all jobs."""
import datetime as dt
import logging
import uuid
from typing import Optional

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from src.config import config

logger = logging.getLogger(__name__)

# Scopes determine what the service account can do.
# These two cover reading/writing sheets and finding them by ID.
_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Column order MUST match the header row in your Google Sheet.
# If you add a column, add it here AND in the sheet.
COLUMNS = [
    "id",
    "added_at",
    "source",
    "company",
    "title",
    "location",
    "url",
    "jd_summary",
    "fit_score",
    "score_reasoning",
    "status",
    "applied_at",
    "cold_email_sent_at",
    "follow_up_due",
    "contacts",
    "cover_letter",
    "notes",
]

# Cache the sheet handle so we don't re-authenticate on every call.
_sheet = None


def _get_sheet():
    """Lazy-init the sheet connection. Called by every public function."""
    global _sheet
    if _sheet is None:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            str(config.SERVICE_ACCOUNT_PATH), _SCOPE
        )
        client = gspread.authorize(creds)
        _sheet = client.open_by_key(config.GOOGLE_SHEET_ID).sheet1
        logger.info(f"Connected to sheet: {_sheet.title}")
    return _sheet


def add_job(
    *,
    source: str,
    company: str,
    title: str,
    location: str,
    url: str,
    jd_summary: str = "",
    fit_score: Optional[float] = None,
    score_reasoning: str = "",
    status: str = "new",
    cover_letter: str = "",
    notes: str = "",
) -> str:
    """Append a new job row. Returns the assigned UUID."""
    sheet = _get_sheet()
    job_id = str(uuid.uuid4())[:8]  # short UUID like 'a3f2c1d9'
    now = dt.datetime.now().isoformat(timespec="seconds")

    row = [
        job_id,
        now,
        source,
        company,
        title,
        location,
        url,
        jd_summary[:200],  # truncate for readability in sheet
        f"{fit_score:.0f}" if fit_score is not None else "",
        score_reasoning[:300],
        status,
        "",   # applied_at (filled later)
        "",   # cold_email_sent_at (filled later)
        "",   # follow_up_due (filled later)
        "",   # contacts (filled later, will be JSON string)
        cover_letter[:5000] if cover_letter else "",
        notes[:1000],
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")
    logger.info(f"Added job {job_id}: {company} — {title}")
    return job_id


def url_exists(url: str) -> bool:
    """Deduplication check. True if this URL is already tracked."""
    sheet = _get_sheet()
    # Column G is the URL column (1-indexed: id=1, added_at=2, source=3, company=4, title=5, location=6, url=7)
    urls = sheet.col_values(7)
    return url.strip() in urls


def get_all_jobs() -> list[dict]:
    """Return all jobs as a list of dicts, keyed by column name."""
    sheet = _get_sheet()
    return sheet.get_all_records()


def get_jobs_by_status(status: str) -> list[dict]:
    """Return all jobs with a specific status."""
    return [j for j in get_all_jobs() if j.get("status") == status]


def update_status(job_id: str, status: str, mark_applied: bool = False) -> bool:
    """Update a job's status. Optionally stamp applied_at timestamp.
    Returns True if the job was found and updated."""
    sheet = _get_sheet()
    cell = sheet.find(job_id)
    if not cell:
        logger.warning(f"Job {job_id} not found")
        return False

    # Column K is status (1-indexed position 11)
    sheet.update_cell(cell.row, 11, status)

    if mark_applied:
        now = dt.datetime.now().isoformat(timespec="seconds")
        sheet.update_cell(cell.row, 12, now)  # column L = applied_at

    logger.info(f"Updated job {job_id} → status={status}")
    return True