---
description: Read-only snapshot of account, positions, open orders, and stops. No state changes.
---

Print a clean ad-hoc portfolio snapshot. No orders placed, no files written.

1. python tools/alpaca.py account
2. python tools/alpaca.py positions
3. python tools/alpaca.py orders

Format the output as:

Portfolio — <today's date>
Equity: $X | Cash: $X (X%) | Buying power: $X
Daytrade count: N | PDT restricted: <yes/no>

Positions:
  SYM | Shares | Entry -> Now | Unrealized P&L ($) | Unrealized P&L (%) | Stop

Open orders:
  TYPE | SYM | qty | trail%/stop_price | order_id

No commentary unless something requires attention:
- Flag any position that has no associated stop order
- Flag any stop order where the stop price is above current bid (stop already triggered or misconfigured)
