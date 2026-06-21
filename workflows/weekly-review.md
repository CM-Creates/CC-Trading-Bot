# Weekly Review Workflow

**When:** Fridays at 4:00 PM CT  
**Objective:** Grade the week, update strategy if warranted, send weekly Slack recap  
**Tools:** `python tools/alpaca.py`, `python tools/perplexity.py`, `python tools/slack.py`  
**Writes:** `memory/WEEKLY-REVIEW.md`, optionally `memory/TRADING-STRATEGY.md`  
**Commits:** Always (mandatory)

---

## Steps

1. **Read memory for full week context**
   - `memory/WEEKLY-REVIEW.md` — note the existing format exactly; new entry must match
   - All TRADE-LOG entries from Monday through today (this full week)
   - All RESEARCH-LOG entries from Monday through today
   - `memory/TRADING-STRATEGY.md` — current rules (needed to evaluate if anything should change)

2. **Pull week-end state**
   ```
   python tools/alpaca.py account
   python tools/alpaca.py positions
   ```

3. **Compute the week's metrics**
   - `starting_equity` = Monday AM equity (from Monday's first EOD snapshot in TRADE-LOG)
   - `ending_equity` = today's `account.equity`
   - Week return ($) = `ending_equity` - `starting_equity`
   - Week return (%) = Week return / `starting_equity` × 100
   - S&P 500 week return:
     ```
     python tools/perplexity.py "S&P 500 total return percentage for the week ending YYYY-MM-DD"
     ```
   - Bot alpha = Bot week % - S&P 500 week %
   - Closed trades this week: count wins, losses, open remaining
   - Win rate = wins / (wins + losses) × 100 (closed only)
   - Best trade: ticker and % gain
   - Worst trade: ticker and % loss  
   - Profit factor = sum(winning realized P&L) / |sum(losing realized P&L)| — use 0 if no closed trades

4. **Append full review to `memory/WEEKLY-REVIEW.md`**
   Match the existing template exactly. Include:
   - Stats table (all metrics from step 3)
   - Closed trades table (ticker, entry, exit, P&L, notes)
   - Open positions at week end (ticker, entry, close, unrealized, stop)
   - What worked (3-5 bullets)
   - What didn't work (3-5 bullets)
   - Key lessons learned
   - Adjustments for next week
   - Overall letter grade A–F

5. **Strategy update (only if warranted)**
   Trigger conditions:
   - A rule has proven itself consistently for 2+ weeks running
   - A rule failed badly this week (caused material losses or missed clear opportunities)
   
   If either applies: update `memory/TRADING-STRATEGY.md` and explicitly call out the change in the "Adjustments for Next Week" section. Do not update the strategy based on a single bad week without clear systemic evidence.

6. **Send ONE Slack message**
   ```
   python tools/slack.py "Week ending MMM DD
   Portfolio: $X (±X% week | ±X% phase)
   vs S&P 500: ±X%
   Trades: N (W:X / L:Y / open:Z)
   Best: SYM +X%  |  Worst: SYM -X%
   Takeaway: <one sentence>
   Grade: <letter>"
   ```

7. **Commit and push** — always mandatory
   ```bash
   git add memory/WEEKLY-REVIEW.md
   # Only add TRADING-STRATEGY.md if it was changed in step 5:
   git add memory/TRADING-STRATEGY.md
   git commit -m "weekly review YYYY-MM-DD"
   git push origin main
   ```
   On push conflict: `git pull --rebase origin main` then retry.

---

## Edge Cases

- **No trades this week:** Stats table shows all zeros/N/A. Grade based on research quality and discipline. Still commit.
- **Perplexity unavailable for S&P return:** Use WebSearch to find the week's S&P performance. Note the source.
- **Starting equity not found in TRADE-LOG:** Use the equity from the most recent available snapshot before Monday.
- **TRADING-STRATEGY.md update is ambiguous:** Default to no change. The rule should be updated only with clear evidence, not as a reaction to a single week's emotion.
