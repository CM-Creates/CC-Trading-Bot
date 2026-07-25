---
description: Run the market-open execution workflow manually. Validates rules, executes approved trades, places stops, logs to TRADE-LOG.md.
---

Run the MARKET-OPEN EXECUTION workflow locally (ad-hoc mode).

Execute the full procedure defined in `workflows/market-open.md` — that file is the
single source of truth for every step, the buy-side gate, quote/spread validation,
the bars sanity-check, stop-placement, and log format. Follow it exactly; do not
shortcut the gate checks.

Local-mode overrides:
- Credentials come from `.env` (the Python tools load it automatically).
- Do NOT run the final "Commit and push" step — local/ad-hoc runs never commit.
