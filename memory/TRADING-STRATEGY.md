# Trading Strategy

## Mission
Beat the S&P 500 over the challenge window. Stocks only — no options, ever.

## Capital & Constraints
- Starting capital: $100,000 (Alpaca paper default)
- Platform: Alpaca (paper trading)
- Instruments: Stocks ONLY — no options, no warrants, no leveraged ETFs
- No PDT restriction: account equity is $100k (above the $25k threshold), so day-trade count is unlimited. This is still a swing strategy, not a day-trading one — the limiter is "max 3 new trades/week," not PDT.

## Core Rules

1. **NO OPTIONS** — ever. Not even "just this once."
2. **75-85% deployed** — target keeps capital working without going all-in
3. **Max 5-6 open positions** — concentration enables conviction
4. **Max 20% of equity per position** — single name can't blow up the portfolio
5. **10% trailing stop on every position as a real GTC order** — never mental stops
6. **Cut losers at -7% manually** — if unrealized loss hits -7%, close immediately, no hoping
7. **Tighten trailing stop to 7% when up +15%, to 5% when up +20%** — protect gains
8. **Never tighten a stop within 3% of current price** — leaves no room for normal noise
9. **Never move a stop down** — stops only move in the favorable direction
10. **Max 3 new trades per week** — overtrading is a cost center
11. **Follow sector momentum** — exit an entire sector after 2 consecutive failed trades in that sector
12. **Patience > activity** — a week with zero trades can be the right answer

## Buy-Side Gate (all must pass before placing any order)

- [ ] Total positions after this fill will be no more than 6
- [ ] Total trades placed this week (including this one) is no more than 3
- [ ] Position cost (shares × ask) is no more than 20% of account equity
- [ ] Position cost is no more than available cash
- [ ] A specific catalyst is documented in today's RESEARCH-LOG entry
- [ ] The instrument is a stock (not an option or anything else)

If any check fails → skip the trade, log the reason, move on.

## Sell-Side Rules

Evaluated at midday scan and opportunistically throughout the day:
- Unrealized loss <= -7% → close immediately
- Thesis broke (catalyst invalidated, sector rolling over, material news event) → close even if not at -7%
- Unrealized gain >= +20% → tighten trailing stop to 5%
- Unrealized gain >= +15% → tighten trailing stop to 7%
- Sector has 2 consecutive failed trades → exit all positions in that sector

## Entry Checklist

Before placing any buy, document all four in the RESEARCH-LOG:
1. What is the specific catalyst today?
2. Is the sector in momentum (not rolling over)?
3. What is the stop level (7-10% below entry)?
4. What is the target (minimum 2:1 risk/reward)?

## Alpaca API Notes

- `trail_percent` and `qty` in order JSON must be **strings** ("10", not 10)
- Quote endpoint: `data.alpaca.markets` (different from trading endpoint)
- `quote.ap` = ask price, `quote.bp` = bid price
- Wide spread or zero values = halted/illiquid → skip the ticker
- Trailing stops only work during market hours; overnight gaps can blow through them
- Stop-order fallback if a stop is ever rejected: trailing_stop → fixed stop → queue for tomorrow AM
