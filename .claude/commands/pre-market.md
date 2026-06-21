---
description: Run the pre-market research workflow manually. Reads memory, pulls account state, researches via Perplexity, writes to RESEARCH-LOG.md.
---

Run the pre-market research workflow locally. Credentials come from .env.
Do NOT git commit or push at the end — this is local/ad-hoc mode.

STEP 1 — Read memory for context:
- memory/TRADING-STRATEGY.md
- tail of memory/TRADE-LOG.md
- tail of memory/RESEARCH-LOG.md

STEP 2 — Pull live account state:
  python tools/alpaca.py account
  python tools/alpaca.py positions
  python tools/alpaca.py orders

STEP 3 — Research market context via Perplexity. Run
python tools/perplexity.py "<query>" for each:
- "WTI and Brent oil price right now"
- "S&P 500 futures premarket today"
- "VIX level today"
- "Top stock market catalysts today"
- "Earnings reports today before market open"
- "Economic calendar today CPI PPI FOMC jobs data"
- "S&P 500 sector momentum YTD"
- One query per currently-held ticker: "news on TICKER today"
If perplexity.py exits 3, fall back to native WebSearch and note the fallback.

STEP 4 — Write a dated entry to memory/RESEARCH-LOG.md using the standard format:
## YYYY-MM-DD — Pre-market Research
### Account
### Market Context
### Held Positions News
### Trade Ideas
### Risk Factors
### Decision: TRADE or HOLD

STEP 5 — Notification: silent unless urgent.
  python tools/slack.py "<one-line alert if needed>"
