---
description: Manual trade helper with full strategy-rule validation. Usage: /trade SYMBOL SHARES buy|sell
---

Execute a manual trade with full rule validation. Refuse if any rule fails.

Args: SYMBOL SHARES SIDE (buy or sell). If any are missing, ask before proceeding.

1. Pull live state:
   python tools/alpaca.py account
   python tools/alpaca.py positions
   python tools/alpaca.py quote SYMBOL
   Capture ask price (P) from quote response.

2. For BUY — validate ALL of the following. If any fail, STOP and print which checks failed:
   - Total positions after this fill will be no more than 6
   - Total trades placed this week + 1 <= 3 (check memory/TRADE-LOG.md for this week's count)
   - SHARES × P <= 20% of account equity
   - SHARES × P <= available cash
   - A specific catalyst exists (ask the user for the thesis if today's RESEARCH-LOG has no entry)
   - Instrument is a stock (confirm SYMBOL is not an option ticker)

3. For SELL — confirm position exists with at least SHARES shares. No other checks required.

4. Print the order JSON and all validation results. Ask "execute? (y/n)" before placing anything.

5. On "y" confirm:
   python tools/alpaca.py order '{"symbol":"SYMBOL","qty":"SHARES","side":"buy","type":"market","time_in_force":"day"}'

6. For BUYs only: immediately place 10% trailing stop GTC after fill confirmed:
   python tools/alpaca.py order '{"symbol":"SYMBOL","qty":"SHARES","side":"sell","type":"trailing_stop","trail_percent":"10","time_in_force":"gtc"}'
   If Alpaca rejects the trailing stop, fall back to fixed stop 10% below fill price:
   python tools/alpaca.py order '{"symbol":"SYMBOL","qty":"SHARES","side":"sell","type":"stop","stop_price":"X.XX","time_in_force":"gtc"}'

7. Append to memory/TRADE-LOG.md:
   ## <date> — Trade: BUY/SELL SYMBOL
   - Shares: N | Entry: $X | Stop: $X (-X%) | Target: $X (X:1 R:R)
   - Thesis: <user-provided catalyst>
   - Stop order ID: <id>

8. python tools/slack.py "Manual trade: BOUGHT/SOLD SYMBOL (N sh @ $X) — <one-line thesis>"
