#!/usr/bin/env python3
"""Render output/digest-content.json and send via Gmail SMTP."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from agent.render import render_email
from agent.send import digest_subject, send_email_smtp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("send-digest")

DIGEST_PATH = ROOT / "output" / "digest-content.json"
PREVIEW_PATH = ROOT / "output" / "latest-digest.html"


def main() -> int:
    recipient = os.getenv("GMAIL_RECIPIENT")
    gmail_user = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not recipient:
        log.error("GMAIL_RECIPIENT not set.")
        return 1
    if not gmail_user or not app_password:
        log.error("GMAIL_USER and GMAIL_APP_PASSWORD must be set.")
        return 1
    if not DIGEST_PATH.is_file():
        log.error("Digest file not found: %s", DIGEST_PATH)
        return 1

    log.info("Loading digest from %s", DIGEST_PATH)
    digest = json.loads(DIGEST_PATH.read_text(encoding="utf-8"))

    log.info("Rendering HTML email...")
    html = render_email(digest)

    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.write_text(html, encoding="utf-8")
    log.info("Preview saved to %s", PREVIEW_PATH)

    subject = digest_subject(digest.get("date"))
    try:
        send_email_smtp(html, recipient, subject)
    except Exception:
        log.exception("Failed to send digest via Gmail SMTP")
        return 1

    log.info("Digest sent successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
