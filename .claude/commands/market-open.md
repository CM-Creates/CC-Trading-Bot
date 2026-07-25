---
description: Run the market-open execution workflow manually. Validates rules, executes approved trades, places stops, logs to TRADE-LOG.md.
---

Run the market-open execution workflow locally. Credentials come from .env.
Do NOT git commit or push at the end — this is local/ad-hoc mode.

STEP 1 — Read memory for today's plan:
- memory/TRADING-STRATEGY.md
- TODAY's entry in memory/RESEARCH-LOG.md
  (if missing, run pre-market STEPS 1-3 inline before continuing)
- tail of memory/TRADE-LOG.md (count trades this week)

STEP 2 — Re-validate each planned trade with fresh live data:
  python tools/alpaca.py account
  python tools/alpaca.py positions
  python tools/alpaca.py quote <each planned ticker>
Skip any ticker with a wide or zero bid/ask spread.

STEP 3 — Hard-check rules BEFORE every order. Skip and log reason if any fail:
- Total positions after fill <= 6
- Trades this week <= 3
- Position cost <= 20% of equity
- Position cost <= available cash
- Catalyst documented in today's RESEARCH-LOG
- Instrument is a stock

STEP 4 — Execute approved buys:
  python tools/alpaca.py order '{"symbol":"SYM","qty":"N","side":"buy","type":"market","time_in_force":"day"}'
Wait for fill before placing stop.

STEP 5 — Place 10% trailing stop GTC for each fill:
  python tools/alpaca.py order '{"symbol":"SYM","qty":"N","side":"sell","type":"trailing_stop","trail_percent":"10","time_in_force":"gtc"}'
Fall back to fixed stop if the trailing stop is rejected. Log "stop rejected" if both fail.

STEP 6 — Append each trade to memory/TRADE-LOG.md.

STEP 7 — Notification only if trades placed:
  python tools/slack.py "Trades: BOUGHT SYM (N sh @ $X) — <why>"
