# Daily Summary Workflow

**When:** Weekdays at 3:00 PM CT, after market close  
**Objective:** Snapshot portfolio state, compute day P&L, send daily Slack recap  
**Tools:** `python tools/alpaca.py`, `python tools/slack.py`  
**Writes:** `memory/TRADE-LOG.md`  
**Commits:** Always (mandatory — tomorrow's P&L math depends on this)

---

## Steps

1. **Read memory for continuity**
   - Tail of `memory/TRADE-LOG.md`:
     - Find the most recent "EOD Snapshot" section header — extract the Portfolio equity value as `yesterday_equity`
     - Count all trade entries (BUY/SELL) dated today → "Trades today"
     - Count all trade entries from Monday through today → weekly trade count
   - Note: If no prior EOD snapshot exists (Day 1), use starting capital of $10,000.00

2. **Pull final state of the day**
   ```
   python tools/alpaca.py account      # equity, cash, buying_power
   python tools/alpaca.py positions    # unrealized P&L per position, current prices
   python tools/alpaca.py orders       # pending stops (for the table)
   ```

3. **Compute metrics**
   - `today_equity` = `account.equity`
   - Day P&L ($) = `today_equity` - `yesterday_equity`
   - Day P&L (%) = Day P&L / `yesterday_equity` × 100
   - Phase P&L ($) = `today_equity` - 10000.00 (starting capital)
   - Phase P&L (%) = Phase P&L / 10000.00 × 100
   - Trades today: list tickers or "none"
   - Weekly trade count: N of 3

4. **Append EOD snapshot to `memory/TRADE-LOG.md`**
   ```
   ### MMM DD — EOD Snapshot (Day N, Weekday)
   **Portfolio:** $X | **Cash:** $X (X%) | **Day P&L:** ±$X (±X%) | **Phase P&L:** ±$X (±X%)
   
   | Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
   |--------|--------|-------|-------|---------|----------------|------|
   | SYM    | N      | $X    | $X    | ±X%     | ±$X (±X%)      | $X   |
   
   **Notes:** Plain-english paragraph: what happened today, any notable moves, plan for tomorrow.
   ```

5. **Send ONE Slack message** — always, even on no-trade days
   ```
   python tools/slack.py "EOD MMM DD
   Portfolio: $X (±X% day | ±X% phase)
   Cash: $X (X%)
   Trades today: <list or none> | Week: N/3
   Open positions:
     SYM ±X.X% (stop $X.XX)
   Tomorrow: <one-line plan or 'no plan yet'>"
   ```

6. **Commit and push** — always mandatory
   ```bash
   git add memory/TRADE-LOG.md
   git commit -m "EOD snapshot YYYY-MM-DD"
   git push origin main
   ```
   On push conflict: `git pull --rebase origin main` then retry. This commit must succeed.

---

## Edge Cases

- **No positions:** EOD table shows "none." Slack message still sent. Commit still happens.
- **Can't find yesterday's equity:** Use the most recent EOD snapshot before today. If none exists, use $10,000.00 and note "Day 1 baseline" in the Notes section.
- **Market was closed today (holiday):** Still run if triggered. Note "market closed" in Notes. Slack message still sends. Commit still happens.
