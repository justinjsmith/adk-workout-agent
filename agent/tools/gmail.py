"""Gmail API tools for fetching workout emails."""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from shared.config import COACH_EMAIL, GMAIL_SCOPES, TOKEN_FILE


def _get_gmail_service():
    """Build an authenticated Gmail API service."""
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"Token file not found at {TOKEN_FILE}. Run scripts/oauth_flow.py first."
        )

    token_data = json.loads(TOKEN_FILE.read_text())
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data.get("scopes", GMAIL_SCOPES),
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        TOKEN_FILE.write_text(json.dumps(token_data, indent=2))

    return build("gmail", "v1", credentials=creds)


def _extract_plain_text(payload: dict) -> str:
    """Recursively extract plain text from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return ""

    # Multipart — recurse into parts
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        # Recurse for nested multipart
        text = _extract_plain_text(part)
        if text:
            return text

    return ""


def _strip_reply_chain(text: str) -> str:
    """Strip quoted reply chains from email text.

    Coach emails are typically threaded as 'RE: Practices Week of X/XX/XX'.
    The reply delimiter is usually a line starting with 'From: Soderlund' or
    a standard Gmail '>' quoting prefix block.
    """
    # Pattern 1: Outlook-style reply header
    patterns = [
        r"^From:\s*Soderlund.*$",
        r"^_{10,}",  # Long underscore line (Outlook separator)
        r"^-{10,}",  # Long dash line
        r"^On .+ wrote:$",  # Gmail-style "On Mon, Jan 1, ... wrote:"
    ]

    lines = text.split("\n")
    cutoff = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()
        for pattern in patterns:
            if re.match(pattern, stripped, re.IGNORECASE):
                cutoff = i
                break
        if cutoff < len(lines):
            break

    return "\n".join(lines[:cutoff]).rstrip()


def _get_header(headers: list[dict], name: str) -> str:
    """Get a header value from Gmail message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch_coach_emails(
    max_results: int = 10,
    after_date: str | None = None,
) -> list[dict]:
    """Fetch recent emails from the coach.

    Args:
        max_results: Maximum number of emails to return.
        after_date: Only fetch emails after this date (YYYY/MM/DD format).

    Returns:
        List of dicts with keys: message_id, thread_id, subject, date,
        body (plain text with reply chains stripped), raw_body (full text).
    """
    service = _get_gmail_service()

    query = f"from:{COACH_EMAIL}"
    if after_date:
        query += f" after:{after_date}"

    results = (
        service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    )

    messages = results.get("messages", [])
    emails = []

    for msg_stub in messages:
        msg = (
            service.users().messages().get(userId="me", id=msg_stub["id"], format="full").execute()
        )

        headers = msg.get("payload", {}).get("headers", [])
        subject = _get_header(headers, "Subject")
        date_str = _get_header(headers, "Date")

        # Parse date
        try:
            email_date = parsedate_to_datetime(date_str)
        except Exception:
            email_date = datetime.now(timezone.utc)

        # Extract body
        raw_body = _extract_plain_text(msg.get("payload", {}))
        body = _strip_reply_chain(raw_body)

        emails.append(
            {
                "message_id": msg["id"],
                "thread_id": msg["threadId"],
                "subject": subject,
                "date": email_date.isoformat(),
                "body": body,
                "raw_body": raw_body,
            }
        )

    return emails


def fetch_email_by_id(message_id: str) -> dict:
    """Fetch a single email by Gmail message ID."""
    service = _get_gmail_service()

    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()

    headers = msg.get("payload", {}).get("headers", [])
    subject = _get_header(headers, "Subject")
    date_str = _get_header(headers, "Date")

    try:
        email_date = parsedate_to_datetime(date_str)
    except Exception:
        email_date = datetime.now(timezone.utc)

    raw_body = _extract_plain_text(msg.get("payload", {}))
    body = _strip_reply_chain(raw_body)

    return {
        "message_id": msg["id"],
        "thread_id": msg["threadId"],
        "subject": subject,
        "date": email_date.isoformat(),
        "body": body,
        "raw_body": raw_body,
    }
