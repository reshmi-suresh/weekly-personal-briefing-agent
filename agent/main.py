"""Weekly briefing agent — fetch data via MCP, render digest, send email."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from agent.render import render_email
from agent.send import send_email_smtp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weekly-briefing-agent")

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MCP_BETA = "mcp-client-2025-11-20"


def _import_prompt():
    from agent import prompt as prompt_module

    return prompt_module


def _import_mcp():
    from agent import mcp_config

    return mcp_config


def extract_json(text: str) -> dict:
    """Extract JSON object from Claude response (fenced or raw)."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("No JSON object found in model response")


def extract_text_blocks(response) -> str:
    parts = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)


def create_client():
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set. Copy .env.example to .env for local runs.")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def fetch_digest(client, prompt_module, mcp_config) -> dict:
    log.info("Fetching data via MCP and generating digest JSON...")
    response = client.beta.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=8192,
        system=prompt_module.build_system_prompt(),
        messages=[{"role": "user", "content": prompt_module.build_user_prompt()}],
        mcp_servers=mcp_config.MCP_SERVERS,
        tools=mcp_config.mcp_tools(),
        betas=[MCP_BETA],
    )
    text = extract_text_blocks(response)
    log.info("Digest response received (%d chars).", len(text))
    return extract_json(text)


def main() -> int:
    recipient = os.getenv("GMAIL_RECIPIENT")
    gmail_user = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not recipient:
        log.error("GMAIL_RECIPIENT not set. Copy .env.example to .env.")
        return 1
    if not gmail_user or not app_password:
        log.error(
            "GMAIL_USER and GMAIL_APP_PASSWORD must be set. "
            "Copy .env.example to .env (local) or configure env vars in your Cloud Routine."
        )
        return 1

    prompt_module = _import_prompt()
    mcp_config = _import_mcp()
    client = create_client()

    try:
        digest = fetch_digest(client, prompt_module, mcp_config)
    except Exception as exc:
        log.exception("Failed to generate digest: %s", exc)
        digest = {
            "date": prompt_module.email_subject().replace("Weekly digest — ", ""),
            "headline": "Good morning — here's your week ahead.",
            "tldr": ["Digest generation failed — see data source notes."],
            "intro": "The briefing agent could not complete its data fetch.",
            "stats": "0 open to-dos · 0 events · 0 unread emails",
            "todos": [],
            "events": [],
            "emails": [],
            "errors": [str(exc)],
        }

    log.info("Rendering HTML email template...")
    html = render_email(digest)

    digest_json_path = PROJECT_ROOT / "output" / "digest-content.json"
    preview_path = PROJECT_ROOT / "output" / "latest-digest.html"
    digest_json_path.parent.mkdir(parents=True, exist_ok=True)
    digest_json_path.write_text(json.dumps(digest, indent=2), encoding="utf-8")
    preview_path.write_text(html, encoding="utf-8")
    log.info("Digest JSON saved to %s", digest_json_path)
    log.info("Preview saved to %s", preview_path)

    try:
        send_email_smtp(html, recipient, prompt_module.email_subject())
        log.info("Weekly digest sent successfully.")
    except Exception as exc:
        log.exception("Failed to send email via Gmail SMTP: %s", exc)
        log.info("HTML preview is available at %s", preview_path)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
