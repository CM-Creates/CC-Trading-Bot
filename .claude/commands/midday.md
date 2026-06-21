---
description: Run the midday scan manually. Cuts losers at -7%, tightens stops on winners, checks theses.
---

Run the midday scan workflow locally. Credentials come from .env.
Do NOT git commit or push at the end — this is local/ad-hoc mode.

STEP 1 — Read memory:
- memory/TRADING-STRATEGY.md (exit rules)
- tail of memory/TRADE-LOG.md (entries, theses, stop levels)
- today's memory/RESEARCH-LOG.md entry

STEP 2 — Pull current live state:
  python tools/alpaca.py positions
  python tools/alpaca.py orders

STEP 3 — Cut losers immediately. For every position where unrealized_plpc <= -0.07:
  python tools/alpaca.py close SYM
  python tools/alpaca.py cancel <stop_order_id>
  Log exit to TRADE-LOG: exit price, realized P&L, "cut at -7% per rule".

STEP 4 — Tighten trailing stops on winners:
- up >= +20% → cancel old stop, place new trail_percent "5"
- up >= +15% → cancel old stop, place new trail_percent "7"
Never tighten within 3% of current price. Never move a stop down.

STEP 5 — Thesis check for each remaining position.
If thesis broke intraday, cut even if not at -7%. Document reasoning in TRADE-LOG.

STEP 6 — Optional Perplexity research on sharp movers:
  python tools/perplexity.py "news on SYM today intraday"
Append addendum to RESEARCH-LOG if material.

STEP 7 — Notification only if action was taken:
  python tools/slack.py "Midday: <action summary>"
