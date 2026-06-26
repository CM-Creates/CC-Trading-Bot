# Weekly Review

Friday reviews are appended here. One entry per week.

---

## Entry Template

```
## Week ending YYYY-MM-DD

### Stats
| Metric | Value |
|--------|-------|
| Starting portfolio | $X |
| Ending portfolio | $X |
| Week return | ±$X (±X%) |
| S&P 500 week | ±X% |
| Bot vs S&P | ±X% |
| Trades | N (W:X / L:Y / open:Z) |
| Win rate | X% |
| Best trade | SYM +X% |
| Worst trade | SYM -X% |
| Profit factor | X.XX |

### Closed Trades
| Ticker | Entry | Exit | P&L | Notes |
|--------|-------|------|-----|-------|

### Open Positions at Week End
| Ticker | Entry | Close | Unrealized | Stop |
|--------|-------|-------|------------|------|

### What Worked
- 

### What Didn't Work
- 

### Key Lessons
- 

### Adjustments for Next Week
- 

### Overall Grade: X
```

---

<!-- Weekly review entries appended below -->

## Week ending 2026-06-26

### Stats
| Metric | Value |
|--------|-------|
| Starting portfolio | $100,000.00 |
| Ending portfolio | $99,854.47 |
| Week return | -$145.53 (-0.15%) |
| S&P 500 week | +0.66% |
| Bot vs S&P | -0.81% |
| Trades | 1 (W:0 / L:0 / open:1) |
| Win rate | N/A (no closed trades) |
| Best trade | N/A (no closed trades) |
| Worst trade | N/A (no closed trades) |
| Profit factor | 0.00 (no closed trades) |

### Closed Trades
| Ticker | Entry | Exit | P&L | Notes |
|--------|-------|------|-----|-------|
| — | — | — | — | None closed this week |

### Open Positions at Week End
| Ticker | Entry | Close | Unrealized | Stop |
|--------|-------|-------|------------|------|
| PG | $150.72 | $149.25 | -$145.53 (-0.98%) | $135.79 (10% trailing GTC) |

### What Worked
- Discipline held: 4 sessions of patience rather than forcing a buy into bad data/wide spreads. No rule was broken to chase deployment.
- Buy-side gate correctly rejected MU all week — its paper feed quoted ~10x the real price; trusting it would have caused a catastrophic mis-sized fill.
- First deployment (PG) was clean: tight 0.16% spread, documented staples/defensive catalyst (VIX +7%), 10% GTC trailing stop placed at entry per rule.

### What Didn't Work
- Deployment lagged badly: 0% deployed Mon-Thu, ~15% by Friday close vs the 75-85% target. The portfolio sat idle while the S&P gained +0.66%, producing the -0.81% relative drag despite a nearly-flat absolute week.
- Structural pipeline gap: pre-market research kept surfacing sector ETFs (XLI/XLP/XLP) which the "Stocks ONLY" rule forbids, leaving no tradeable individual name with a clean feed + catalyst for four days.
- PG entered near the intraday high (-0.98% unrealized at week end) — minor entry-timing slippage.

### Key Lessons
- Patience is a feature, but four days of forced idleness was a tooling/research failure, not pure discipline — research must name specific individual large-cap stocks with verified-clean quotes, not ETFs.
- Always sanity-check a quote against fundamentals before trusting the feed (MU 10x inflation would have been a $100k mistake).
- Being flat in an up week is a guaranteed loss vs benchmark — under-deployment has a real cost even with zero losing trades.

### Adjustments for Next Week
- Pre-market research must output ≥1-2 individual large-cap stocks (NOT ETFs) with documented catalysts and verified-clean quotes in momentum sectors (Energy, Staples, Industrials).
- Move deployment from ~15% toward the 75-85% target: add 2-4 positions as clean candidates appear, max 3 new trades/week, each ≤20% equity.
- Monitor PG vs its $135.79 trailing stop; cut at -7% manually if the staples thesis breaks.
- No strategy-rule changes this week — one week is too small a sample to revise rules. "Stocks ONLY" stays; the fix is at the research layer, not the rulebook.

### Overall Grade: C
- Capital preserved (-0.15%, near flat) and discipline intact, but lost to the benchmark by 0.81% through chronic under-deployment. Average week: avoided mistakes, failed to make money.
