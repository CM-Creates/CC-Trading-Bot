---
description: Run the Friday weekly review manually. Computes week stats, appends review to WEEKLY-REVIEW.md, sends Slack message.
---

Run the weekly review workflow locally. Credentials come from .env.
Do NOT git commit or push at the end — this is local/ad-hoc mode.

STEP 1 — Read memory for full week context:
- memory/WEEKLY-REVIEW.md (match existing template for your new entry)
- ALL this week's entries in memory/TRADE-LOG.md
- ALL this week's entries in memory/RESEARCH-LOG.md
- memory/TRADING-STRATEGY.md

STEP 2 — Pull week-end state:
  python tools/alpaca.py account
  python tools/alpaca.py positions

STEP 3 — Compute metrics:
- Starting equity (Monday AM), ending equity, week return ($ and %)
- S&P 500 week return: python tools/perplexity.py "S&P 500 weekly return week ending <date>"
- W/L/open trade counts, win rate, best trade, worst trade, profit factor

STEP 4 — Append full review section to memory/WEEKLY-REVIEW.md using standard template.

STEP 5 — Update memory/TRADING-STRATEGY.md if a rule proved out or failed badly (ask before writing).

STEP 6 — Send ONE Slack message:
  python tools/slack.py "Week ending <date>: $X (±X% week | ±X% phase) vs S&P ±X% — Grade: X"
