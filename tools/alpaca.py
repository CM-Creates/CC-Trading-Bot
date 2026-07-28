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


def _raise_for_alpaca(r):
    # Distinguish auth failure (keys set but rejected) from every other error so
    # the caller gets a clear, actionable message instead of a raw traceback.
    # Exit 2 = auth failure specifically (keys present but invalid/expired/revoked).
    if r.status_code in (401, 403):
        print(
            f"ERROR: Alpaca auth failed (HTTP {r.status_code}). "
            "ALPACA_API_KEY / ALPACA_SECRET_KEY are set but invalid, expired, or revoked. "
            "Regenerate the paper keys in the Alpaca dashboard and update the routine environment. "
            f"Response: {r.text.strip()[:200]}",
            file=sys.stderr,
        )
        sys.exit(2)
    r.raise_for_status()


def _get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    _raise_for_alpaca(r)
    return r.json()


def _post(url, body):
    r = requests.post(url, headers=HEADERS, json=body, timeout=15)
    _raise_for_alpaca(r)
    return r.json()


def _delete(url):
    r = requests.delete(url, headers=HEADERS, timeout=15)
    if r.status_code == 204:
        return {}
    _raise_for_alpaca(r)
    try:
        return r.json()
    except Exception:
        return {}


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/alpaca.py <account|positions|position|quote|bars|orders|order|cancel|cancel-all|close|close-all> [args]", file=sys.stderr)
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
            q["tradeable"] = q["spread_pct"] <= 1.0
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

    else:
        print(f"Unknown subcommand: {cmd}", file=sys.stderr)
        print("Usage: python tools/alpaca.py <account|positions|position|quote|bars|orders|order|cancel|cancel-all|close|close-all> [args]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
