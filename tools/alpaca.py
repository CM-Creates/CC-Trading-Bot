#!/usr/bin/env python3
"""
Alpaca v2 API wrapper. All trading API calls go through here.
Usage: python tools/alpaca.py <subcommand> [args...]
"""
import json
import os
import sys
from pathlib import Path

# Load .env if present
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

API_KEY = os.environ.get("ALPACA_API_KEY", "")
SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")

if not API_KEY:
    print("ERROR: ALPACA_API_KEY not set in environment", file=sys.stderr)
    sys.exit(1)
if not SECRET_KEY:
    print("ERROR: ALPACA_SECRET_KEY not set in environment", file=sys.stderr)
    sys.exit(1)

API = os.environ.get("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets/v2")
DATA = os.environ.get("ALPACA_DATA_ENDPOINT", "https://data.alpaca.markets/v2")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
    "Content-Type": "application/json",
}


def _get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _post(url, body):
    r = requests.post(url, headers=HEADERS, json=body, timeout=15)
    r.raise_for_status()
    return r.json()


def _delete(url):
    r = requests.delete(url, headers=HEADERS, timeout=15)
    if r.status_code == 204:
        return {}
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {}


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/alpaca.py <account|positions|position|quote|bars|orders|order|cancel|cancel-all|close|close-all|week-trades> [args]", file=sys.stderr)
        sys.exit(1)

    cmd = args[0]

    if cmd == "account":
        print(json.dumps(_get(f"{API}/account"), indent=2))

    elif cmd == "positions":
        print(json.dumps(_get(f"{API}/positions"), indent=2))

    elif cmd == "position":
        if len(args) < 2:
            print("Usage: python tools/alpaca.py position SYM", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(_get(f"{API}/positions/{args[1].upper()}"), indent=2))

    elif cmd == "quote":
        if len(args) < 2:
            print("Usage: python tools/alpaca.py quote SYM", file=sys.stderr)
            sys.exit(1)
        sym = args[1].upper()
        result = _get(f"{DATA}/stocks/{sym}/quotes/latest")
        q = result.get("quote", {})
        ap, bp = q.get("ap", 0), q.get("bp", 0)
        if ap and bp:
            q["spread_pct"] = round((ap - bp) / ap * 100, 3)
            tradeable = q["spread_pct"] <= 1.0
            # Absolute-price sanity check: a tight spread alone does NOT mean the
            # feed is real. The paper sandbox has quoted names (e.g. MU) ~10x their
            # true price with an internally-consistent (tight) spread. Compare the
            # ask against the most recent daily bar close and reject wild outliers.
            try:
                import datetime
                start = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
                bars = (_get(f"{DATA}/stocks/{sym}/bars",
                             params={"timeframe": "1Day", "start": start, "limit": 1})
                        .get("bars") or [])
                ref = bars[-1].get("c") if bars else None
                if ref:
                    q["ref_close"] = ref
                    ratio = ap / ref
                    q["price_ratio"] = round(ratio, 3)
                    if ratio > 3 or ratio < 0.33:
                        tradeable = False
                        q["feed_warning"] = (
                            f"ask {ap} is {q['price_ratio']}x the recent close {ref} "
                            f"— likely broken feed, DO NOT TRADE"
                        )
                else:
                    q["feed_warning"] = "no reference bar available — verify price manually"
            except Exception as e:
                q["feed_warning"] = f"sanity check failed ({e}) — verify price manually"
            q["tradeable"] = tradeable
        print(json.dumps(result, indent=2))

    elif cmd == "bars":
        if len(args) < 2:
            print("Usage: python tools/alpaca.py bars SYM [timeframe] [limit]", file=sys.stderr)
            print("  timeframe: 1Day (default), 1Hour, 5Min", file=sys.stderr)
            sys.exit(1)
        import datetime
        sym = args[1].upper()
        timeframe = args[2] if len(args) > 2 else "1Day"
        limit = int(args[3]) if len(args) > 3 else 10
        # Start far enough back to guarantee `limit` bars (2x for weekends/holidays)
        start = (datetime.date.today() - datetime.timedelta(days=limit * 2 + 5)).isoformat()
        result = _get(f"{DATA}/stocks/{sym}/bars", params={"timeframe": timeframe, "start": start, "limit": limit})
        bars = result.get("bars") or []
        if not bars:
            print(f"No bars returned for {sym}")
        else:
            for b in bars:
                print(f"  {b.get('t','')[:10]}  o={b.get('o')}  h={b.get('h')}  l={b.get('l')}  c={b.get('c')}  v={b.get('v')}")

    elif cmd == "orders":
        status = args[1] if len(args) > 1 else "open"
        print(json.dumps(_get(f"{API}/orders", params={"status": status}), indent=2))

    elif cmd == "order":
        if len(args) < 2:
            print("Usage: python tools/alpaca.py order '<json>'", file=sys.stderr)
            sys.exit(1)
        body = json.loads(args[1])
        print(json.dumps(_post(f"{API}/orders", body), indent=2))

    elif cmd == "cancel":
        if len(args) < 2:
            print("Usage: python tools/alpaca.py cancel ORDER_ID", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(_delete(f"{API}/orders/{args[1]}"), indent=2))

    elif cmd == "cancel-all":
        print(json.dumps(_delete(f"{API}/orders"), indent=2))

    elif cmd == "close":
        if len(args) < 2:
            print("Usage: python tools/alpaca.py close SYM", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(_delete(f"{API}/positions/{args[1].upper()}"), indent=2))

    elif cmd == "close-all":
        print(json.dumps(_delete(f"{API}/positions"), indent=2))

    elif cmd == "week-trades":
        # Deterministic "max 3 new trades per week" counter. Source of truth is
        # Alpaca's filled-order history, NOT the markdown log (which is tallied by
        # eye and drifts). Counts filled BUY orders since Monday 00:00 America/Chicago.
        import datetime
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Chicago")
        except Exception:
            tz = datetime.timezone.utc
        now = datetime.datetime.now(tz)
        monday = (now - datetime.timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)
        after_utc = monday.astimezone(datetime.timezone.utc).isoformat()
        orders = _get(f"{API}/orders", params={
            "status": "closed", "after": after_utc, "limit": 500, "direction": "asc"})
        buys = [o for o in orders
                if o.get("side") == "buy" and o.get("filled_at")
                and float(o.get("filled_qty") or 0) > 0]
        limit = 3
        count = len(buys)
        out = {
            "week_start_ct": monday.date().isoformat(),
            "new_trades_this_week": count,
            "weekly_limit": limit,
            "room_left": max(0, limit - count),
            "gate_open": count < limit,
            "buys": [{"symbol": o.get("symbol"), "filled_qty": o.get("filled_qty"),
                      "filled_at": o.get("filled_at")} for o in buys],
        }
        print(json.dumps(out, indent=2))

    else:
        print(f"Unknown subcommand: {cmd}", file=sys.stderr)
        print("Usage: python tools/alpaca.py <account|positions|position|quote|bars|orders|order|cancel|cancel-all|close|close-all|week-trades> [args]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
