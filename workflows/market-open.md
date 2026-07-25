# Market-Open Execution Workflow

**When:** Weekdays at 10:00 AM CT (90 min after open — spreads normalized)  
**Objective:** Execute planned trades from today's research, set stops on every new position  
**Tools:** `python tools/alpaca.py`, `python tools/perplexity.py`, `python tools/slack.py`  
**Writes:** `memory/TRADE-LOG.md`  
**Commits:** Only if trades executed

---

## Steps

1. **Read memory for today's plan**
   - `memory/TRADING-STRATEGY.md` — hard rules (especially buy-side gate)
   - Today's entry in `memory/RESEARCH-LOG.md` — the trade ideas and catalyst list
   - Last 50 lines of `memory/TRADE-LOG.md` — open positions, entries, recent context
   
   If today's RESEARCH-LOG entry is missing, run pre-market STEPS 1-3 inline first. Never trade without documented research.

   Then get the authoritative weekly-trade count (do NOT tally it by eye from the log):
   ```
   python tools/alpaca.py week-trades
   ```
   Use `new_trades_this_week` / `room_left` / `gate_open` from this output for the 3/week cap in STEP 3.

2. **Re-validate with fresh live data**
   ```
   python tools/alpaca.py account
   python tools/alpaca.py positions
   python tools/alpaca.py quote SYM    # for each planned ticker
   ```
   Check `spread_pct` in quote response. Skip the ticker if `spread_pct > 1.0` or if `tradeable: false` — indicates stale/after-hours data or genuinely illiquid market. Normal large-cap spread is under 0.1%; anything above 1% is a bad quote window.
   If the ask price looks wildly different from the research price target, run:
   ```
   python tools/alpaca.py bars SYM 1Day 5
   ```
   to pull 5 days of OHLC bars and sanity-check the current price against recent history. If quote price is outside 2× the recent high, treat the quote as bad data and skip.

3. **Run buy-side gate on each planned trade**
   Every single check must pass or the trade is skipped:
   - Total positions after fill <= 6
   - `new_trades_this_week` (from `alpaca.py week-trades`) + trades about to place this run <= 3
   - Position cost (shares × ask) <= 20% of account equity
   - Position cost <= available cash
   - Specific catalyst documented in today's RESEARCH-LOG
   - Instrument is a stock (not option, warrant, or ETF derivative)
   
   Log any skipped trades with the specific rule that failed.

4. **Execute approved buys**
   ```
   python tools/alpaca.py order '{"symbol":"SYM","qty":"N","side":"buy","type":"market","time_in_force":"day"}'
   ```
   Check order status before placing the stop — wait for `status: filled`.

5. **Immediately place 10% trailing stop GTC**
   ```
   python tools/alpaca.py order '{"symbol":"SYM","qty":"N","side":"sell","type":"trailing_stop","trail_percent":"10","time_in_force":"gtc"}'
   ```
   - `trail_percent` and `qty` must be strings ("10", not 10)
   - If Alpaca rejects the trailing stop, fall back to fixed stop ~10% below fill price
   - If fixed stop is also blocked, log "stop rejected, set tomorrow AM" in TRADE-LOG

6. **Append trade entries to `memory/TRADE-LOG.md`**
   One section per trade:
   ```
   ## YYYY-MM-DD — Trade: BUY SYM
   - Shares: N | Entry: $X | Stop: $X (-X%) | Target: $X (X:1 R:R)
   - Thesis: <one sentence catalyst>
   - Stop order ID: <id>
   ```

7. **Notification** — only if at least one trade placed
   ```
   python tools/slack.py "Trades YYYY-MM-DD: BOUGHT SYM (N sh @ $X) — <one-line why>"
   ```

8. **Commit and push** — only if trades executed; skip if no trades fired
   ```bash
   git add memory/TRADE-LOG.md
   git commit -m "market-open trades YYYY-MM-DD"
   git push origin main
   ```

---

## Edge Cases

- **No trade ideas in RESEARCH-LOG:** Do nothing. Log "no trades — no research entry" and exit.
- **All planned trades fail gate checks:** Log each failure, send no notification, do not commit.
- **Fill confirmed but stop rejected:** Log the rejection and queue the stop for tomorrow's market-open routine.
- **Quote shows zero spread or no data:** Skip that ticker, note it in TRADE-LOG as "skipped — illiquid/halted."
