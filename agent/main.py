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
TEMPLATE_PATH = AGENT_DIR / "templates" / "email.html"

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weekly-briefing-agent")

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
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


def markdown_bold_to_html(text: str) -> str:
    """Convert **bold** markdown to HTML strong tags."""
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_tldr_items(items: list[str]) -> str:
    if not items:
        return '<li style="margin-bottom:8px;">Nothing critical flagged this week.</li>'
    return "".join(
        f'<li style="margin-bottom:8px;">{html_escape(item)}</li>' for item in items
    )


def render_todo_items(todos: list[dict]) -> str:
    if not todos:
        return (
            '<li style="margin-bottom:12px;font-family:Arial,Helvetica,sans-serif;'
            'font-size:15px;color:#888888;">No open to-dos.</li>'
        )
    rows = []
    for todo in todos:
        text = html_escape(todo.get("text", ""))
        date = todo.get("suggested_date")
        date_html = ""
        if date:
            date_html = (
                f'<span style="margin-left:8px;font-size:12px;color:#888888;">'
                f"→ {html_escape(date)}</span>"
            )
        rows.append(
            '<li style="margin-bottom:12px;font-family:Arial,Helvetica,sans-serif;'
            'font-size:15px;line-height:1.5;">'
            '<span style="display:inline-block;width:14px;height:14px;'
            'border:1.5px solid #000000;border-radius:50%;margin-right:10px;'
            'vertical-align:middle;"></span>'
            f"{text}{date_html}</li>"
        )
    return "".join(rows)


def render_event_items(events: list[dict]) -> str:
    if not events:
        return (
            '<p style="margin:0;font-family:Arial,Helvetica,sans-serif;'
            'font-size:15px;color:#888888;">No events this week.</p>'
        )

    blocks = []
    for event in events:
        day = html_escape(event.get("day", ""))
        name = html_escape(event.get("name", ""))
        time = html_escape(event.get("time", ""))
        location = event.get("location")
        loc_html = ""
        if location:
            loc_html = (
                f' · <span style="color:#888888;">{html_escape(location)}</span>'
            )

        prep_notes = event.get("prep_notes") or []
        prep_html = ""
        if prep_notes:
            notes = "".join(
                f'<li style="margin-bottom:4px;">{html_escape(n)}</li>'
                for n in prep_notes
            )
            prep_html = (
                '<ul style="margin:8px 0 0 0;padding-left:20px;'
                'font-family:Arial,Helvetica,sans-serif;font-size:14px;'
                'line-height:1.5;color:#333333;">'
                f"{notes}</ul>"
            )

        blocks.append(
            '<div style="margin-bottom:20px;">'
            f'<p style="margin:0 0 4px 0;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:12px;color:#888888;">{day}</p>'
            f'<p style="margin:0;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:16px;line-height:1.5;">'
            f"<strong>{name}</strong> · {time}{loc_html}</p>"
            f"{prep_html}</div>"
        )
    return "".join(blocks)


def render_email_items(emails: list[dict]) -> str:
    if not emails:
        return (
            '<p style="margin:0;font-family:Arial,Helvetica,sans-serif;'
            'font-size:15px;color:#888888;">Inbox clear — no unread emails.</p>'
        )

    blocks = []
    for email in emails:
        urgent = email.get("urgent", False)
        urgent_badge = ""
        if urgent:
            urgent_badge = (
                '<span style="margin-left:8px;padding:2px 6px;'
                'font-family:Arial,Helvetica,sans-serif;font-size:10px;'
                'letter-spacing:0.05em;text-transform:uppercase;'
                'background-color:#000000;color:#ffffff;">Urgent</span>'
            )
        blocks.append(
            '<div style="margin-bottom:18px;padding-bottom:18px;'
            'border-bottom:1px solid #f0f0f0;">'
            f'<p style="margin:0 0 4px 0;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:15px;"><strong>{html_escape(email.get("sender", ""))}</strong>'
            f"{urgent_badge}</p>"
            f'<p style="margin:0 0 4px 0;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:15px;">{html_escape(email.get("subject", ""))}</p>'
            f'<p style="margin:0 0 6px 0;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:14px;line-height:1.5;color:#444444;">'
            f'{html_escape(email.get("preview", ""))}</p>'
            f'<p style="margin:0;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:12px;color:#888888;">'
            f'{html_escape(email.get("timestamp", ""))}</p></div>'
        )
    return "".join(blocks)


def render_errors_section(errors: list[str]) -> str:
    if not errors:
        return ""
    items = "".join(
        f'<li style="margin-bottom:6px;">{html_escape(err)}</li>' for err in errors
    )
    return (
        '<tr><td style="padding:28px 0;border-bottom:1px solid #e0e0e0;">'
        '<h2 style="margin:0 0 12px 0;font-family:Georgia,serif;font-size:18px;">'
        "Data source notes</h2>"
        f'<ul style="margin:0;padding-left:20px;font-family:Arial,sans-serif;'
        f'font-size:14px;color:#666666;">{items}</ul></td></tr>'
    )


def render_email(data: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "{{DATE}}": html_escape(data.get("date", "")),
        "{{HEADLINE}}": html_escape(
            data.get("headline", "Good morning — here's your week ahead.")
        ),
        "{{TLDR_ITEMS}}": render_tldr_items(data.get("tldr", [])),
        "{{INTRO}}": markdown_bold_to_html(data.get("intro", "")),
        "{{STATS}}": html_escape(data.get("stats", "")),
        "{{TODO_ITEMS}}": render_todo_items(data.get("todos", [])),
        "{{EVENT_ITEMS}}": render_event_items(data.get("events", [])),
        "{{EMAIL_ITEMS}}": render_email_items(data.get("emails", [])),
        "{{ERRORS_SECTION}}": render_errors_section(data.get("errors", [])),
    }
    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)
    return html


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


def send_email_via_mcp(client, prompt_module, mcp_config, html: str, recipient: str):
    subject = prompt_module.email_subject()
    log.info("Sending digest to %s via Gmail MCP...", recipient)
    response = client.beta.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt_module.build_send_email_prompt(
                    recipient, subject, html
                ),
            }
        ],
        mcp_servers=mcp_config.GMAIL_ONLY_SERVERS,
        tools=mcp_config.mcp_tools(["gmail"]),
        betas=[MCP_BETA],
    )
    text = extract_text_blocks(response)
    log.info("Send response: %s", text[:500])
    return text


def main() -> int:
    recipient = os.getenv("GMAIL_RECIPIENT")
    if not recipient:
        log.error("GMAIL_RECIPIENT not set. Copy .env.example to .env.")
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

    preview_path = PROJECT_ROOT / "output" / "latest-digest.html"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_text(html, encoding="utf-8")
    log.info("Preview saved to %s", preview_path)

    try:
        send_email_via_mcp(client, prompt_module, mcp_config, html, recipient)
        log.info("Weekly digest sent successfully.")
    except Exception as exc:
        log.exception("Failed to send email via Gmail MCP: %s", exc)
        log.info("HTML preview is available at %s", preview_path)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
