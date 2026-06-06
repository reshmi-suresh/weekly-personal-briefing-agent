# Claude Cloud Routine setup

This agent is designed to run on **Claude Premium / Claude Code Cloud Routines** at [claude.ai/code/scheduled](https://claude.ai/code/scheduled). Authentication for Gmail, Google Calendar, and Notion is handled by your Claude session — no API keys are stored in the routine.

For local development and testing, use `python agent/main.py` with an `ANTHROPIC_API_KEY` in `.env` (see README).

---

## 1. Create a new Cloud Routine

1. Go to [claude.ai/code/scheduled](https://claude.ai/code/scheduled).
2. Click **New routine** (or equivalent).
3. Name it **Weekly briefing agent**.

---

## 2. Connect MCP servers

Add these three remote MCP servers in the routine's MCP settings:

| Name | URL |
|------|-----|
| `gmail` | `https://gmailmcp.googleapis.com/mcp/v1` |
| `google-calendar` | `https://calendarmcp.googleapis.com/mcp/v1` |
| `notion` | `https://mcp.notion.com/mcp` |

Complete OAuth for each service when prompted (Gmail, Google Calendar, Notion workspace access).

---

## 3. Schedule

| Setting | Value |
|---------|-------|
| Frequency | Weekly |
| Day | Sunday |
| Time | Morning (e.g. 7:00 AM in your timezone) |

---

## 4. Prompt to paste

Copy the system prompt from `agent/prompt.py` (`build_system_prompt()`), then append this user instruction block:

```
Generate my weekly digest for the next 7 days. Fetch calendar events, incomplete Notion todos, and unread Gmail from the last 7 days.

After fetching data:
1. Return the structured JSON as specified in the system prompt.
2. Render it as a clean HTML email matching the weekly digest layout (serif headline, sans-serif body, inline CSS, checkbox circles for todos, horizontal rules between sections).
3. Send the HTML email to my Gmail inbox using the Gmail MCP send tool.

Subject line: Weekly digest — [today's date]

If a data source fails, continue with the others and note the failure in the email.
```

For Cloud Routines, Claude handles fetch → render → send in one run. The local `agent/main.py` splits render (Python template) and send for reproducible HTML; the routine prompt above inlines that behaviour.

---

## 5. Notion Todo List database

Ensure the Notion MCP has access to your Todo List database:

**Database ID:** `339dea62-56ec-80f9-bee6-000b60295068`

The agent filters for **incomplete tasks only**, ordered by position (lower = lower priority).

---

## 6. Expected output

Each Sunday you should receive an HTML email in your Gmail inbox with:

- **Header** — date, "Weekly digest" label, italic headline
- **TL;DR** — numbered bullets under 15 words each, with section cross-refs
- **Intro** — 2–3 sentences with bold highlights + stat line
- **To-dos** — incomplete Notion tasks with suggested dates
- **This week** — calendar events by day with prep notes
- **Unread emails** — sender, subject, preview, timestamp; urgent items flagged

Tone is factual and direct — no guilt-tripping or editorialising.

---

## 7. Verify it ran

1. **Email** — Check your inbox (and Promotions/Updates tabs) for "Weekly digest — [date]".
2. **Routine history** — In Claude Code scheduled routines, open run history for success/failure logs.
3. **Spot-check data** — Confirm event count matches Google Calendar for the next 7 days and todos match Notion incomplete items.

If a source failed, the email includes a **Data source notes** section listing what could not be fetched.

---

## 8. Troubleshooting

| Issue | Fix |
|-------|-----|
| No email received | Re-authorise Gmail MCP; check spam; confirm routine ran in history |
| Empty calendar/todos | Re-connect Google Calendar / Notion MCP; verify Notion database ID |
| Wrong recipient | Cloud Routine uses your connected Gmail account |
| Duplicate attendees | Prompt aliases personal/work/Jamie emails — ensure system prompt is included |

---

## Local fallback (GitHub Actions)

See `.github/workflows/weekly.yml` for an optional Sunday cron that runs `agent/main.py` if you prefer CI over Cloud Routines. Requires repository secrets: `ANTHROPIC_API_KEY`, `GMAIL_RECIPIENT`.
