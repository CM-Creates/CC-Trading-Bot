---
description: Run the pre-market research workflow manually. Reads memory, pulls account state, researches via Perplexity, writes to RESEARCH-LOG.md.
---

Run the PRE-MARKET RESEARCH workflow locally (ad-hoc mode).

Execute the full procedure defined in `workflows/pre-market.md` — that file is the
single source of truth for every step, tool call, query list, output format, and
edge case. Follow it exactly.

Local-mode overrides:
- Credentials come from `.env` (the Python tools load it automatically).
- Do NOT run the final "Commit and push" step — local/ad-hoc runs never commit.
