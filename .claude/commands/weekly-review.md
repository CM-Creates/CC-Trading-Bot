---
description: Run the Friday weekly review manually. Computes week stats, appends review to WEEKLY-REVIEW.md, sends Slack message.
---

Run the WEEKLY REVIEW workflow locally (ad-hoc mode).

Execute the full procedure defined in `workflows/weekly-review.md` — that file is the
single source of truth for every step, the week metrics, the review template, the
strategy-update criteria, and the Slack message. Follow it exactly.

Local-mode overrides:
- Credentials come from `.env` (the Python tools load it automatically).
- If the workflow's strategy-update step would modify memory/TRADING-STRATEGY.md,
  ASK before writing — do not change the rulebook unattended in a local run.
- Do NOT run the final "Commit and push" step — local/ad-hoc runs never commit.
