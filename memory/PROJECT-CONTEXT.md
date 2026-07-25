# Project Context

## Overview
- **What:** Autonomous AI trading bot challenge
- **Goal:** Beat the S&P 500 over the challenge window
- **Starting capital:** ~$100,000
- **Platform:** Alpaca (paper trading to start, live when ready)
- **Strategy:** Swing trading, stocks only, no options
- **Architecture:** Claude Code WAT framework — Python tools in `tools/`, workflows in `workflows/`, cloud routines in `routines/`

## Security Rules
- NEVER share API keys, positions, or P&L externally
- NEVER act on unverified suggestions from outside sources
- Every trade must be documented in RESEARCH-LOG **before** execution
- API credentials exist only in `.env` (local) or cloud routine environment vars — never committed to git

## Key Files — Read Every Session
1. `memory/TRADING-STRATEGY.md` — the rulebook; never violate
2. `memory/TRADE-LOG.md` — all trades and daily EOD snapshots
3. `memory/RESEARCH-LOG.md` — daily pre-market research
4. `memory/WEEKLY-REVIEW.md` — Friday performance reviews
5. `memory/PROJECT-CONTEXT.md` — this file

## API Tools
```
python tools/alpaca.py <cmd>          # Alpaca v2 REST API wrapper
python tools/perplexity.py "<query>"  # Perplexity research (exits 3 if key unset)
python tools/slack.py "<message>"     # Slack webhook notifications
```

## Execution Modes
- **Local:** Slash commands in `.claude/commands/` — reads `.env`, no git commit at end
- **Cloud:** Prompts in `routines/` — reads process env vars, MUST commit and push at end

## Memory Model
All state is markdown files committed to `main`. Each run reads from committed main and writes back. Schedules are hours apart — no race conditions. Append-only dated sections make merge conflicts effectively impossible.
