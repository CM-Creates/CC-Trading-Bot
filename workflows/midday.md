# Midday Scan Workflow

**When:** Weekdays at noon CT  
**Objective:** Cut losers, tighten stops on winners, check theses  
**Tools:** `python tools/alpaca.py`, `python tools/perplexity.py`, `python tools/slack.py`  
**Writes:** `memory/TRADE-LOG.md`, optionally `memory/RESEARCH-LOG.md`  
**Commits:** Only if memory files changed

---

## Steps

1. **Read memory**
   - `memory/TRADING-STRATEGY.md` — exit rules specifically
   - Last 100 lines of `memory/TRADE-LOG.md` — original entry prices, thesis, stop order IDs
   - Today's `memory/RESEARCH-LOG.md` entry — original thesis and risk factors

2. **Pull current live state**
   ```
   python tools/alpaca.py positions    # unrealized_plpc is the key field
   python tools/alpaca.py orders       # need stop order IDs for cancellation
   ```

3. **Cut losers immediately**
   For every position where `unrealized_plpc` (decimal) <= -0.07:
   ```
   python tools/alpaca.py close SYM
   python tools/alpaca.py cancel <stop_order_id>
   ```
   Log in TRADE-LOG:
   ```
   ## YYYY-MM-DD — Exit: SOLD SYM (stopped out)
   - Exit price: $X | Realized P&L: -$X (-X%) | Reason: cut at -7% per rule
   ```

4. **Tighten trailing stops on winners**
   Check `unrealized_plpc` for each remaining position:
   - `>= 0.20` → tighten to `trail_percent: "5"`
   - `>= 0.15` → tighten to `trail_percent: "7"`
   
   Before tightening, calculate: current_price × (1 - new_trail_pct). If that floor is within 3% of current price, do NOT tighten — would violate the 3% guardrail.
   Never move a stop down.
   ```
   python tools/alpaca.py cancel <old_stop_order_id>
   python tools/alpaca.py order '{"symbol":"SYM","qty":"N","side":"sell","type":"trailing_stop","trail_percent":"5","time_in_force":"gtc"}'
   ```
   Log: "Tightened SYM trail to 5% at +X%"

5. **Thesis check**
   For each remaining open position, mentally review: Is the original catalyst still intact? Is price action consistent with the thesis? Any material midday news?
   If the thesis has broken (catalyst invalidated, sector rolling over, unexpected news):
   ```
   python tools/alpaca.py close SYM
   python tools/alpaca.py cancel <stop_order_id>
   ```
   Log the specific reason in TRADE-LOG — do not just say "thesis broken."

6. **Optional intraday research**
   If any position moved >3% in either direction with no obvious cause:
   ```
   python tools/perplexity.py "news on SYM today intraday YYYY-MM-DD"
   ```
   If findings are material, append an afternoon addendum to `memory/RESEARCH-LOG.md`.

7. **Notification** — only if action was taken
   ```
   python tools/slack.py "Midday YYYY-MM-DD: <brief summary of what was done>"
   ```

8. **Commit and push** — only if memory files changed; skip if no-op
   ```bash
   git add memory/TRADE-LOG.md memory/RESEARCH-LOG.md
   git commit -m "midday scan YYYY-MM-DD"
   git push origin main
   ```

---

## Edge Cases

- **No positions:** Pull state, confirm no positions, exit silently. No commit.
- **Sector rule triggered (2 consecutive losses in same sector):** Close all positions in that sector, even if not at -7%. Log clearly in TRADE-LOG.
- **Perplexity unavailable:** Fall back to WebSearch for intraday research.
- **Stop cancel fails (order already filled/expired):** Log the attempt and continue. Position may already be closed.
