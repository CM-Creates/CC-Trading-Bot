# Cloud Routine Prompts

Paste each file's contents verbatim into its Claude Code cloud routine. Do not paraphrase — the env-var check block and the commit/push step are load-bearing.

| File | Cron (America/Chicago) | Time |
|------|------------------------|------|
| pre-market.md | `0 6 * * 1-5` | 6:00 AM weekdays |
| market-open.md | `0 10 * * 1-5` | 10:00 AM weekdays |
| midday.md | `0 12 * * 1-5` | Noon weekdays |
| daily-summary.md | `0 15 * * 1-5` | 3:00 PM weekdays |
| weekly-review.md | `0 16 * * 5` | 4:00 PM Fridays |

## One-time setup (do once before creating routines)

1. Install the Claude GitHub App on this repo
2. In each routine's environment settings, toggle **"Allow unrestricted branch pushes"** ON
3. Add all env vars from `env.template` to each routine's environment config (NOT a .env file)
4. After creating each routine, click **"Run now"** to verify before waiting for the cron
