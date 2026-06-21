# Pre-Market Research Workflow

**When:** Weekdays at 6:00 AM CT, before market open  
**Objective:** Research today's catalysts and write actionable trade ideas to RESEARCH-LOG.md  
**Tools:** `python tools/alpaca.py`, `python tools/perplexity.py`, `python tools/slack.py`  
**Writes:** `memory/RESEARCH-LOG.md`  
**Commits:** Yes (mandatory)

---

## Steps

1. **Read memory for context**
   - `memory/TRADING-STRATEGY.md` — rules and constraints
   - Last 50 lines of `memory/TRADE-LOG.md` — open positions, recent entries
   - Last 20 lines of `memory/RESEARCH-LOG.md` — yesterday's setup

2. **Pull live account state**
   ```
   python tools/alpaca.py account     # equity, cash, buying_power, daytrade_count
   python tools/alpaca.py positions   # open positions with unrealized P&L
   python tools/alpaca.py orders      # pending GTC stops
   ```

3. **Research market context via Perplexity**
   Run one query at a time:
   - Oil prices (WTI and Brent)
   - S&P 500 futures premarket
   - VIX level
   - Top catalysts for today's date
   - Earnings before market open
   - Economic calendar (CPI, PPI, FOMC, jobs)
   - S&P 500 sector momentum YTD
   - News on each currently-held ticker
   
   If `perplexity.py` exits with code 3 (key unset), fall back to native WebSearch and note the fallback in the log.

4. **Write dated entry to `memory/RESEARCH-LOG.md`**
   Include: account snapshot, market context, 2-3 trade ideas with catalyst/entry/stop/target, risk factors, and a trade/hold decision (default HOLD).

5. **Notification**
   Silent unless urgent: a held position is already -7% in pre-market, thesis broke overnight, or major macro event. If urgent: `python tools/slack.py "<one-line alert>"`

6. **Commit and push**
   ```bash
   git add memory/RESEARCH-LOG.md
   git commit -m "pre-market research YYYY-MM-DD"
   git push origin main
   ```
   On push conflict: `git pull --rebase origin main` then retry. Never force-push.

---

## Edge Cases

- **No PERPLEXITY_API_KEY:** Fall back to WebSearch. Note fallback in the log entry.
- **Alpaca shows a position already down -7%:** Skip the normal research flow, immediately note the emergency in Slack, then proceed with research.
- **No positions held:** Skip the per-ticker news queries. Focus on new idea generation.
- **Research log already has today's entry:** Append an "update" section rather than overwriting.
