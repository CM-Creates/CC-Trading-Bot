---
description: Run the midday scan manually. Cuts losers at -7%, tightens stops on winners, checks theses.
---

Run the MIDDAY SCAN workflow locally (ad-hoc mode).

Execute the full procedure defined in `workflows/midday.md` — that file is the
single source of truth for every step, the -7% cut rule, the +15%/+20% stop-tighten
thresholds, the 3% guardrail, and log formats. Follow it exactly; do not improvise
the thresholds.

Local-mode overrides:
- Credentials come from `.env` (the Python tools load it automatically).
- Do NOT run the final "Commit and push" step — local/ad-hoc runs never commit.
