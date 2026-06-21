---
description: Run the daily summary workflow manually. Computes day P&L, appends EOD snapshot to TRADE-LOG.md, sends Slack message.
---

Run the daily summary workflow locally. Credentials come from .env.
Do NOT git commit or push at the end — this is local/ad-hoc mode.

STEP 1 — Read memory for continuity:
- tail of memory/TRADE-LOG.md
  Find yesterday's EOD snapshot equity for Day P&L math.
  Count today's trades and this week's trades.

STEP 2 — Pull final state of the day:
  python tools/alpaca.py account
  python tools/alpaca.py positions
  python tools/alpaca.py orders

STEP 3 — Compute metrics:
- Day P&L ($ and %) = today_equity - yesterday_equity
- Phase P&L ($ and %) = today_equity - 10000.00
- Trades today: list tickers or "none"
- Trades this week: running count

STEP 4 — Append EOD snapshot to memory/TRADE-LOG.md using standard format.

STEP 5 — Send ONE Slack message (always, even no-trade days):
  python tools/slack.py "EOD <date>: $X (±X% day | ±X% phase) — <positions summary>"
