#!/usr/bin/env python3
"""
Build script for the public Hermes site. Reads memory/*.md and live Alpaca
account state, writes docs/data/{home,news,insights,portfolio}.json.

Usage: python tools/site_build.py

Called from every workflows/*.md routine (pre-market, market-open, midday,
daily-summary, weekly-review) so the public site refreshes on the same
schedule as the trading automation itself.
Reuses tools/dashboard.py's "latest entry" parsers for snapshot values; adds
its own full-history walks for the News and Insights pages (dashboard.py only
ever needs the latest entry, so it doesn't do that).
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import dashboard as db  # noqa: E402  (reuse latest-entry parsers + format helpers)

TRADE_LOG = ROOT / "memory" / "TRADE-LOG.md"
RESEARCH_LOG = ROOT / "memory" / "RESEARCH-LOG.md"
WEEKLY_REVIEW = ROOT / "memory" / "WEEKLY-REVIEW.md"
DATA_DIR = ROOT / "docs" / "data"


def clean_dashes(value):
    """Normalize em/en dashes to a plain hyphen for site typography.

    Source memory/*.md entries are quoted verbatim for authenticity, but they
    were written with em-dashes; the site's house style is hyphen-only, so we
    normalize punctuation without touching any facts or numbers.
    """
    if isinstance(value, str):
        return value.replace("—", "-").replace("–", "-")
    if isinstance(value, list):
        return [clean_dashes(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_dashes(v) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# Live Alpaca state
# ---------------------------------------------------------------------------

def alpaca_json(*args):
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "alpaca.py"), *args],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"[site_build] WARN: alpaca.py {' '.join(args)} failed: {result.stderr.strip()}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"[site_build] WARN: could not parse alpaca.py {' '.join(args)} output", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Full-history parsers (dashboard.py's parsers only keep the latest entry)
# ---------------------------------------------------------------------------

def parse_trade_entries(path: Path) -> list:
    """Every '## DATE — Trade: BUY/SELL TICKER' section, chronological."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    entries = []
    for section in re.split(r"\n---\n", text):
        m = re.search(r"^##\s+(\d{4}-\d{2}-\d{2})\s*[—-]+\s*Trade:\s*(BUY|SELL)\s+([A-Z]+)",
                       section, re.MULTILINE)
        if not m:
            continue
        date_str, side, ticker = m.group(1), m.group(2), m.group(3)
        detail = re.search(
            r"Shares:\s*([\d,]+)[^|]*\|\s*Entry:\s*\$([\d,.]+)[^|]*\|\s*Stop:\s*\$([\d,.]+)[^|]*\|\s*Target:\s*\$([\d,.]+)",
            section,
        )
        thesis_m = re.search(r"Thesis:\s*(.+)", section)
        order_m = re.search(r"Stop order ID:\s*(\S+)", section)
        entries.append({
            "date": date_str, "side": side, "ticker": ticker,
            "shares": detail.group(1) if detail else None,
            "entry": detail.group(2) if detail else None,
            "stop": detail.group(3) if detail else None,
            "target": detail.group(4) if detail else None,
            "thesis": thesis_m.group(1).strip() if thesis_m else "",
            "stop_order_id": order_m.group(1) if order_m else None,
        })
    return entries


def eod_equity_series(path: Path) -> list:
    """Every EOD Snapshot's portfolio equity, in file (chronological) order.

    Feeds the equity sparkline on the site's featured equity metric. Section
    headers ("### Jun 23 - EOD Snapshot ...") aren't ISO dates, so the series
    is an ordered list of equity floats; the sparkline only needs the shape.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    equities = []
    for section in re.split(r"\n---\n", text):
        if "EOD Snapshot" not in section:
            continue
        m = re.search(r"\*\*Portfolio:\*\*\s*\$([\d,]+\.?\d*)", section)
        if m:
            equities.append(round(float(m.group(1).replace(",", "")), 2))
    return equities


def first_and_last_eod_equity(path: Path):
    """(first, last) equity values across every EOD Snapshot section, in file order."""
    series = eod_equity_series(path)
    if not series:
        return None, None
    return series[0], series[-1]


def _bullets(section_text: str, heading: str) -> list:
    sec = re.search(rf"### {re.escape(heading)}\s*\n(.+?)(?=###|\Z)", section_text, re.DOTALL)
    out = []
    if sec:
        for line in sec.group(1).strip().split("\n"):
            line = re.sub(r"^\s*[-*]\s*", "", line).strip()
            if line:
                out.append(line)
    return out


def parse_research_full(path: Path) -> list:
    """Every dated '## YYYY-MM-DD — ...' section in RESEARCH-LOG.md, ascending."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    clean = db.strip_fenced(text)
    parts = re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", clean)
    dated = [p.strip() for p in parts if re.match(r"## \d{4}-\d{2}-\d{2}", p.strip())]

    entries = []
    for p in dated:
        m = re.match(r"## (\d{4}-\d{2}-\d{2})\s*[—-]+\s*(.+)", p)
        date_str = m.group(1) if m else ""
        title = m.group(2).strip() if m else ""

        decision = "HOLD"
        decision_text = ""
        dec_section = re.search(r"### Decision\s*\n(.+?)(?=###|\Z)", p, re.DOTALL)
        if dec_section:
            decision_text = dec_section.group(1).strip()
            if re.search(r"\bTRADE\b", decision_text, re.IGNORECASE) and \
               not re.search(r"\bHOLD\b", decision_text, re.IGNORECASE):
                decision = "TRADE"

        market_lines = []
        ctx = re.search(r"### (?:Market Context|Key Catalysts)\s*\n(.+?)(?=###|\Z)", p, re.DOTALL)
        if ctx:
            for line in ctx.group(1).strip().split("\n"):
                line = re.sub(r"^\s*[-*]\s*", "", line).strip()
                if line and len(line) > 8:
                    market_lines.append(line)

        ideas = []
        ideas_sec = re.search(r"### Trade Ideas\s*\n(.+?)(?=###|\Z)", p, re.DOTALL)
        if ideas_sec:
            for line in ideas_sec.group(1).strip().split("\n"):
                line = re.sub(r"^\s*\d+\.\s*", "", line).strip()
                if line:
                    ideas.append(line)

        risks = _bullets(p, "Risk Factors")

        entries.append({
            "date": date_str,
            "title": title,
            "type": "research",
            "decision": decision,
            "decision_text": decision_text[:400],
            "market_lines": market_lines[:8],
            "trade_ideas": ideas[:4],
            "risk_factors": risks[:5],
        })
    return entries


def parse_weekly_full(path: Path) -> list:
    """Every '## Week ending ...' section in WEEKLY-REVIEW.md, ascending."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    clean = db.strip_fenced(text)
    if "## Week ending" not in clean:
        return []
    parts = re.split(r"\n(?=## Week ending)", clean)
    weeks = [p for p in parts if p.strip().startswith("## Week ending")]

    out = []
    for w in weeks:
        m = re.search(r"## Week ending\s+(\S+)", w)
        week_end = m.group(1) if m else ""

        stats = {}
        stats_sec = re.search(r"### Stats\s*\n(.+?)(?=###|\Z)", w, re.DOTALL)
        if stats_sec:
            for row in re.finditer(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", stats_sec.group(1)):
                key = row.group(1).strip().lower().replace(" ", "_").replace("&", "and")
                val = row.group(2).strip()
                if key not in ("metric", "---", "------", "value") and not re.match(r"^-+$", key):
                    stats[key] = val

        def _table(heading, cols):
            rows_out = []
            sec = re.search(rf"### {re.escape(heading)}\s*\n(.+?)(?=###|\Z)", w, re.DOTALL)
            if not sec:
                return rows_out
            lines = [l for l in sec.group(1).strip().split("\n") if l.strip().startswith("|")]
            for line in lines[2:]:  # skip header + separator row
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= len(cols) and cells[0] not in ("—", "-", ""):
                    rows_out.append(dict(zip(cols, cells)))
            return rows_out

        closed_trades = _table("Closed Trades", ["ticker", "entry", "exit", "pnl", "notes"])
        open_positions = _table("Open Positions at Week End", ["ticker", "entry", "close", "unrealized", "stop"])

        grade_m = re.search(r"Overall Grade:\s*(\w+)", w)

        out.append({
            "week_end": week_end,
            "stats": stats,
            "closed_trades": closed_trades,
            "open_positions": open_positions,
            "what_worked": _bullets(w, "What Worked"),
            "what_didnt": _bullets(w, "What Didn't Work"),
            "key_lessons": _bullets(w, "Key Lessons"),
            "adjustments": _bullets(w, "Adjustments for Next Week"),
            "grade": grade_m.group(1) if grade_m else stats.get("overall_grade", "-"),
        })
    return out


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def main():
    now = datetime.now(timezone.utc)
    generated_at = now.strftime("%Y-%m-%d %H:%M UTC")

    account = alpaca_json("account") or {}
    live_positions = alpaca_json("positions") or []
    open_orders = alpaca_json("orders", "open") or []

    trade = db.parse_trade_log(TRADE_LOG)
    trade_entries = parse_trade_entries(TRADE_LOG)
    equity_series = eod_equity_series(TRADE_LOG)
    first_equity = equity_series[0] if equity_series else None
    last_logged_equity = equity_series[-1] if equity_series else None
    research_history = parse_research_full(RESEARCH_LOG)
    weekly_history = parse_weekly_full(WEEKLY_REVIEW)
    latest_research = db.parse_research_log(RESEARCH_LOG)

    live_equity = float(account.get("equity")) if account.get("equity") is not None else None
    live_cash = float(account.get("cash")) if account.get("cash") is not None else None
    cash_pct = round(live_cash / live_equity * 100, 1) if live_equity else None

    # Equity sparkline series: EOD snapshots plus the fresher live value, so the
    # curve ends on the same number the big featured value animates to.
    spark_series = list(equity_series)
    if live_equity is not None and (not spark_series or spark_series[-1] != round(live_equity, 2)):
        spark_series.append(round(live_equity, 2))

    day_pnl = day_pnl_pct = phase_pnl = phase_pnl_pct = None
    if live_equity is not None and last_logged_equity is not None:
        day_pnl = round(live_equity - last_logged_equity, 2)
        day_pnl_pct = round(day_pnl / last_logged_equity * 100, 2)
    if live_equity is not None and first_equity:
        phase_pnl = round(live_equity - first_equity, 2)
        phase_pnl_pct = round(phase_pnl / first_equity * 100, 2)

    days_live = None
    created_at = account.get("created_at")
    if created_at:
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            days_live = (now - created_dt).days
        except ValueError:
            pass

    # Merge live positions with logged stop orders + thesis
    stop_by_symbol = {}
    for o in open_orders:
        if o.get("order_type") == "trailing_stop" and o.get("side") == "sell":
            stop_by_symbol[o["symbol"]] = {
                "stop_price": o.get("stop_price"),
                "trail_percent": o.get("trail_percent"),
                "hwm": o.get("hwm"),
            }
    thesis_by_symbol = {}
    for e in trade_entries:
        if e["side"] == "BUY":
            thesis_by_symbol[e["ticker"]] = {"thesis": e["thesis"], "target": e["target"], "date": e["date"]}

    positions_out = []
    for p in live_positions:
        sym = p.get("symbol")
        stop_info = stop_by_symbol.get(sym, {})
        thesis_info = thesis_by_symbol.get(sym, {})
        positions_out.append({
            "ticker": sym,
            "qty": p.get("qty"),
            "entry": p.get("avg_entry_price"),
            "current": p.get("current_price"),
            "market_value": p.get("market_value"),
            "unrealized_pl": p.get("unrealized_pl"),
            "unrealized_plpc": p.get("unrealized_plpc"),
            "stop_price": stop_info.get("stop_price"),
            "trail_percent": stop_info.get("trail_percent"),
            "thesis": thesis_info.get("thesis", ""),
            "target": thesis_info.get("target"),
            "entry_date": thesis_info.get("date"),
        })

    # ---- portfolio.json ----
    portfolio = {
        "generated_at": generated_at,
        "snapshot_date": now.strftime("%Y-%m-%d"),
        "account": {
            "equity": live_equity,
            "cash": live_cash,
            "cash_pct": cash_pct,
            "buying_power": account.get("buying_power"),
            "portfolio_value": account.get("portfolio_value"),
        },
        "positions": positions_out,
        "day_pnl": day_pnl,
        "day_pnl_pct": day_pnl_pct,
        "phase_pnl": phase_pnl,
        "phase_pnl_pct": phase_pnl_pct,
        "equity_series": spark_series,
        "trade_history": list(reversed(trade_entries)),
    }

    # ---- news.json ----
    trade_news_items = [{
        "date": e["date"], "type": "trade", "ticker": e["ticker"], "side": e["side"],
        "shares": e["shares"], "entry": e["entry"], "stop": e["stop"], "target": e["target"],
        "thesis": e["thesis"],
    } for e in trade_entries]
    news_items = research_history + trade_news_items
    news_items.sort(key=lambda x: x["date"], reverse=True)
    news = {"generated_at": generated_at, "items": news_items}

    # ---- insights.json ----
    insights = {
        "generated_at": generated_at,
        "weekly": list(reversed(weekly_history)),
        "sector_momentum": latest_research.get("sectors", []) if latest_research else [],
        "macro_snapshot": {
            "date": latest_research.get("date") if latest_research else None,
            "market_lines": latest_research.get("market_lines", []) if latest_research else [],
        },
    }

    # ---- home.json ----
    recent_activity = []
    for item in news_items[:3]:
        if item["type"] == "trade":
            thesis = item["thesis"]
            if len(thesis) > 110:
                thesis = thesis[:110].rsplit(" ", 1)[0] + "..."
            summary = f"{item['side']} {item['ticker']}: {thesis}"
        else:
            summary = f"{item.get('title', 'Pre-market research')}: {item.get('decision', 'HOLD')}"
        recent_activity.append({"date": item["date"], "type": item["type"], "summary": summary})

    home = {
        "generated_at": generated_at,
        "equity": live_equity,
        "phase_pnl_pct": phase_pnl_pct,
        "day_pnl_pct": day_pnl_pct,
        "days_live": days_live,
        "open_position_count": len(positions_out),
        "equity_series": spark_series,
        "recent_activity": recent_activity,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, payload in (("portfolio", portfolio), ("news", news), ("insights", insights), ("home", home)):
        clean_payload = clean_dashes(payload)
        (DATA_DIR / f"{name}.json").write_text(json.dumps(clean_payload, indent=2), encoding="utf-8")

    print(f"[site_build] wrote docs/data/*.json at {generated_at}")
    print(f"[site_build]   equity=${live_equity:,.2f}  positions={len(positions_out)}  "
          f"day_pnl_pct={day_pnl_pct}%  phase_pnl_pct={phase_pnl_pct}%")
    print(f"[site_build]   news items={len(news_items)}  weekly reviews={len(weekly_history)}")


if __name__ == "__main__":
    main()
