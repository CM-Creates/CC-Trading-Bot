# Autonomous Trading Bot

Autonomous swing-trading agent built on the Claude Code WAT framework. Runs on a daily cron schedule via Claude Code cloud routines. Paper trades stocks on Alpaca, researches via Perplexity, notifies via Slack.

## Prerequisites

- Alpaca paper trading account (alpaca.markets)
- Perplexity API key (perplexity.ai/api)
- Slack incoming webhook URL
- GitHub account (for cloud routines)
- Python 3.9+ with `requests` library (`pip install requests python-dotenv`)

## Local Setup

1. Copy `env.template` to `.env` and fill in your credentials
2. Open this repo in Claude Code
3. Run `/portfolio` to verify the Alpaca connection

## Cloud Routines

Configure five routines in the Claude Code web UI using the prompts in `routines/`. Set the cron schedules (America/Chicago):

| Routine        | Cron          | Time (CT)        |
|----------------|---------------|------------------|
| pre-market     | `0 6 * * 1-5` | 6:00 AM weekdays |
| market-open    | `0 10 * * 1-5`| 10:00 AM weekdays |
| midday         | `0 12 * * 1-5`| Noon weekdays    |
| daily-summary  | `0 15 * * 1-5`| 3:00 PM weekdays |
| weekly-review  | `0 16 * * 5`  | 4:00 PM Fridays  |

**Required cloud routine settings:**
- Select this GitHub repo, branch: `main`
- Add all env vars from `env.template` to the routine's environment config
- Toggle **"Allow unrestricted branch pushes"** ON (most common setup failure)

## Directory Layout

```
tools/          Python API wrappers (Alpaca, Perplexity, Slack)
workflows/      WAT Layer 1 SOPs — THE single source of truth for each procedure
routines/       Cloud routine prompts — thin wrappers that delegate to workflows/
memory/         Persistent agent state — committed to main after every run
.claude/commands/  Local slash commands — thin wrappers that delegate to workflows/
```

**Single source of truth:** each procedure's steps live in exactly one file under
`workflows/`. The matching `routines/*.md` (cloud) and `.claude/commands/*.md` (local)
files are thin wrappers that reference the workflow and add only their mode-specific
parts — cloud adds the env-var check and mandatory commit/push; local reads `.env`
and never commits. Edit the procedure in `workflows/` only; the wrappers rarely change.

## Smoke Test

```bash
python tools/alpaca.py account      # should return account JSON
python tools/perplexity.py "VIX"    # should return research text
python tools/slack.py "test"        # should post to your Slack channel
```
