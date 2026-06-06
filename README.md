# weekly-briefing-agent

A personal weekly briefing agent that connects to **Gmail**, **Google Calendar**, and **Notion** via MCP (Model Context Protocol), generates a structured weekly digest, and sends it as an HTML email every Sunday.

Designed to run on **Claude Premium / Claude Code Cloud Routines** — no API key required in production. The code here supports local development, testing, and Cloud Routine prompt configuration.

---

## What it does

Every Sunday (or on manual trigger):

1. **Fetches** calendar events for the next 7 days, incomplete Notion todos, and unread Gmail from the last 7 days
2. **Synthesises** a factual weekly digest with TL;DR, intro, todos, calendar prep notes, and unread email summary
3. **Renders** a clean HTML email from `agent/templates/email.html`
4. **Sends** the digest to your Gmail inbox via the Gmail MCP

If a data source fails, the agent continues with the others and notes the failure in the email.

---

## Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| LLM | Claude (Anthropic API / Cloud Routines) |
| Integrations | MCP — Gmail, Google Calendar, Notion |
| Email | HTML template with inline CSS |
| Scheduling | Claude Cloud Routine (primary), GitHub Actions (optional fallback) |

---

## MCP server URLs

| Service | URL |
|---------|-----|
| Gmail | `https://gmailmcp.googleapis.com/mcp/v1` |
| Google Calendar | `https://calendarmcp.googleapis.com/mcp/v1` |
| Notion | `https://mcp.notion.com/mcp` |

**Notion Todo List database ID:** `339dea62-56ec-80f9-bee6-000b60295068`

---

## Prerequisites

- **Production:** Claude Premium with Cloud Routines access at [claude.ai/code/scheduled](https://claude.ai/code/scheduled)
- **Local testing:** Python 3.11+, Anthropic API key, OAuth access to MCP servers via your Claude/API session
- Connected accounts: Gmail, Google Calendar, Notion (with access to the Todo List database)

---

## Local setup

```bash
git clone <repo-url>
cd weekly-briefing-agent

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=your_key_here        # local testing only
GMAIL_RECIPIENT=your@gmail.com
NOTION_TODO_DB=339dea62-56ec-80f9-bee6-000b60295068
```

> MCP authentication for Gmail, Calendar, and Notion is handled by Claude's session in Cloud Routines. For local API runs, your Anthropic account must have MCP OAuth configured for the connected servers.

---

## Run manually

From the project root:

```bash
python agent/main.py
```

Or use the helper script (creates venv if missing):

```bash
bash scripts/run.sh
```

On success:

- Digest email is sent to `GMAIL_RECIPIENT`
- HTML preview is saved to `output/latest-digest.html`

---

## Project structure

```
weekly-briefing-agent/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── agent/
│   ├── main.py               # Orchestrates fetch → render → send
│   ├── prompt.py             # System prompt for Claude
│   ├── mcp_config.py         # MCP server definitions
│   └── templates/
│       └── email.html        # HTML email template
├── scripts/
│   └── run.sh                # Local manual trigger
├── docs/
│   └── cloud-routine.md      # Cloud Routine setup guide
└── .github/
    └── workflows/
        └── weekly.yml        # Optional GitHub Actions fallback
```

---

## Claude Cloud Routine (recommended)

For production scheduling without maintaining API keys:

1. Follow **[docs/cloud-routine.md](docs/cloud-routine.md)**
2. Connect the three MCP servers listed above
3. Paste the system prompt from `agent/prompt.py`
4. Schedule: **weekly, Sunday morning**

Cloud Routines handle MCP auth via your Claude session — no credentials in code.

---

## GitHub Actions fallback (optional)

`.github/workflows/weekly.yml` runs every Sunday at 07:00 UTC (adjust the cron for your timezone).

Add repository secrets:

- `ANTHROPIC_API_KEY`
- `GMAIL_RECIPIENT`

Trigger manually via **Actions → Weekly Briefing → Run workflow**.

---

## Email design

The HTML template uses:

- Serif headline font (Georgia), sans-serif body (Arial)
- White background, black text, generous whitespace
- Horizontal rules between sections
- Checkbox circles (styled spans) for todos
- Muted grey timestamps and tags
- Mobile-responsive layout (max-width 600px)

---

## License

MIT (or your preferred license)
