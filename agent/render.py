"""Render weekly digest JSON into HTML email."""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "email.html"


def html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def markdown_bold_to_html(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


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
