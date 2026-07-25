---
description: Run the daily summary workflow manually. Computes day P&L, appends EOD snapshot to TRADE-LOG.md, sends Slack message.
---

Run the DAILY SUMMARY workflow locally (ad-hoc mode).

Execute the full procedure defined in `workflows/daily-summary.md` — that file is the
single source of truth for every step, the P&L math (starting capital $100,000.00),
the EOD snapshot format, and the Slack message. Follow it exactly.

Local-mode overrides:
- Credentials come from `.env` (the Python tools load it automatically).
- Do NOT run the final "Commit and push" step — local/ad-hoc runs never commit.
  (Note: a local run therefore does NOT persist the EOD snapshot the cloud routine
  relies on for tomorrow's Day P&L — use this command for spot checks, not as a
  substitute for the scheduled cloud daily-summary.)
