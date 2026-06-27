#!/usr/bin/env python3
"""
Reads memory/*.md and writes docs/index.html — a self-contained trading dashboard.
Usage: python tools/dashboard.py
"""

import re
import sys
from pathlib import Path
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo('America/Chicago')
except ImportError:
    _TZ = None

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# CSS block (plain string — no f-string escaping needed)
# ---------------------------------------------------------------------------

CSS = """
:root {
  --ink: #f3efe5;
  --muted: #8f9a9f;
  --dim: #56636a;
  --panel: rgba(18, 24, 27, 0.84);
  --panel-strong: rgba(24, 33, 37, 0.92);
  --line: rgba(180, 196, 193, 0.14);
  --line-bright: rgba(207, 220, 216, 0.24);
  --green: #56c78f;
  --red: #e05d5d;
  --amber: #d9a64f;
  --blue: #7ea8a1;
  --violet: #b59ad9;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background:
    radial-gradient(circle at 16% -12%, rgba(126, 168, 161, 0.22), transparent 34rem),
    radial-gradient(circle at 88% 6%, rgba(217, 166, 79, 0.12), transparent 28rem),
    linear-gradient(135deg, #11171a 0%, #0d1113 42%, #161814 100%);
  color: var(--ink);
  font-family: "Aptos", "Segoe UI", "Helvetica Neue", sans-serif;
  min-height: 100vh;
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,0.75), transparent 72%);
}
.wrap {
  max-width: 1380px;
  margin: 0 auto;
  padding: 28px 22px 24px;
  position: relative;
}
.card {
  background: linear-gradient(180deg, var(--panel-strong), var(--panel));
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 18px 52px rgba(0, 0, 0, 0.22);
  overflow: hidden;
}
.metric-card {
  min-height: 138px;
  position: relative;
}
.metric-card::after {
  content: "";
  position: absolute;
  inset: auto 18px 16px 18px;
  height: 3px;
  border-radius: 999px;
  background: var(--accent, var(--line-bright));
  opacity: 0.78;
}
.accent-blue   { --accent: var(--blue); }
.accent-green  { --accent: var(--green); }
.accent-red    { --accent: var(--red); }
.accent-purple { --accent: var(--violet); }
.accent-amber  { --accent: var(--amber); }
.accent-gray   { --accent: var(--line-bright); }
.badge-trade {
  background: rgba(86,199,143,0.12);
  color: var(--green);
  border: 1px solid rgba(86,199,143,0.35);
  border-radius: 999px;
  padding: 9px 22px;
  font-size: 0.92rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  display: inline-block;
  font-weight: 700;
}
.badge-hold {
  background: rgba(217,166,79,0.13);
  color: var(--amber);
  border: 1px solid rgba(217,166,79,0.34);
  border-radius: 999px;
  padding: 9px 22px;
  font-size: 0.92rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  display: inline-block;
  font-weight: 700;
}
.num { font-family: "SFMono-Regular", "Cascadia Code", "Courier New", monospace; font-variant-numeric: tabular-nums; }
.pos { color: var(--green); }
.neg { color: var(--red); }
.neu { color: var(--muted); }
.amb { color: var(--amber); }
.ticker-cell { font-weight: 800; color: var(--ink); }
.muted-cell { color: #a7b1ad; }
.quiet-cell { color: var(--dim); font-size: 0.75rem; }
.label {
  font-size: 0.68rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-weight: 700;
  margin-bottom: 12px;
}
.metric-value {
  font-size: clamp(1.55rem, 2.4vw, 2.15rem);
  font-weight: 760;
  letter-spacing: 0;
}
.metric-sub {
  color: var(--dim);
  font-size: 0.76rem;
  margin-top: 8px;
}
.live-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  margin-right: 6px;
  animation: pulse 2.5s infinite;
  vertical-align: middle;
  box-shadow: 0 0 14px rgba(86,199,143,0.8);
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.15; }
}
.cards-grid {
  display: grid;
  grid-template-columns: 1.25fr repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
@media (max-width: 900px) {
  .cards-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .cards-grid { grid-template-columns: 1fr; }
}
table { border-collapse: collapse; width: 100%; }
th {
  border-bottom: 1px solid var(--line-bright);
  padding: 12px 14px;
  text-align: left;
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 700;
}
td {
  border-bottom: 1px solid var(--line);
  padding: 13px 14px;
  font-size: 0.875rem;
  color: #d9dedb;
}
tr:hover td { background: rgba(255,255,255,0.035); }
.stop-pill {
  background: rgba(126,168,161,0.12);
  color: #a8c5bf;
  border: 1px solid rgba(126,168,161,0.28);
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 0.72rem;
}
.research-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 20px;
}
@media (max-width: 700px) {
  .research-grid { grid-template-columns: 1fr; }
}
.mkt-line {
  padding: 10px 0 10px 18px;
  border-bottom: 1px solid var(--line);
  font-size: 0.84rem;
  color: #c7cfcb;
  line-height: 1.55;
  position: relative;
}
.mkt-line::before {
  content: "";
  position: absolute;
  left: 0;
  top: 17px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--blue);
}
.mkt-line:last-child { border-bottom: none; }
.decision-box {
  background: rgba(8, 12, 13, 0.5);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 12px;
}
.chip {
  background: rgba(255,255,255,0.045);
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 0.78rem;
  white-space: nowrap;
  display: inline-block;
}
.chip-val { color: var(--ink); font-family: "SFMono-Regular", "Cascadia Code", "Courier New", monospace; }
.chips-row { display: flex; flex-wrap: wrap; gap: 10px; padding: 4px 0; }
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  margin-bottom: 18px;
  padding: 22px 0 18px;
  border-bottom: 1px solid var(--line-bright);
}
.brand-kicker {
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.brand-title {
  font-size: clamp(1.75rem, 4vw, 3.45rem);
  line-height: 0.95;
  font-weight: 820;
  letter-spacing: 0;
  margin-top: 8px;
}
.mode-pill {
  background: rgba(217,166,79,0.12);
  color: #e7c17c;
  border: 1px solid rgba(217,166,79,0.3);
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 0.68rem;
  letter-spacing: 0.13em;
  font-weight: 800;
}
.status-line {
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 0.76rem;
}
.no-data {
  text-align: center;
  padding: 34px 0;
  color: var(--dim);
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.table-scroll { overflow-x: auto; margin: 0 -4px; }
.section-stack { display: grid; gap: 16px; }
@media (max-width: 760px) {
  .wrap { padding: 18px 14px; }
  .header-bar { align-items: flex-start; flex-direction: column; }
  .status-line { justify-content: flex-start; }
  .card { padding: 16px; }
  th, td { padding: 11px 10px; }
}
footer {
  text-align: center;
  font-size: 0.68rem;
  color: var(--dim);
  padding: 14px 0 4px;
}
"""

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def strip_fenced(text: str) -> str:
    return re.sub(r'```.*?```', '', text, flags=re.DOTALL)


def parse_trade_log(path: Path) -> dict:
    empty = {'latest': None, 'history': []}
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return empty

    try:
        sections = re.split(r'\n---\n', text)
        entries = []

        for section in sections:
            if 'EOD Snapshot' not in section:
                continue

            entry = {}

            # Header
            m = re.search(r'^###\s+(.+?)\s*[—-]+\s*EOD Snapshot\s*\((.+?)\)', section, re.MULTILINE)
            if not m:
                continue
            entry['date'] = m.group(1).strip()
            entry['day_label'] = m.group(2).strip()

            # Metrics line
            m = re.search(
                r'\*\*Portfolio:\*\*\s*\$([\d,]+\.?\d*)\s*\|'
                r'.*?\*\*Cash:\*\*\s*\$([\d,]+\.?\d*)\s*\(([\d.]+)%\)'
                r'.*?\*\*Day P&L:\*\*\s*([+\-]?\$[\d,.]+)\s*\(([+\-]?[\d.]+)%\)'
                r'.*?\*\*Phase P&L:\*\*\s*([+\-]?\$[\d,.]+)\s*\(([+\-]?[\d.]+)%\)',
                section
            )
            if m:
                entry['equity']         = float(m.group(1).replace(',', ''))
                entry['cash']           = float(m.group(2).replace(',', ''))
                entry['cash_pct']       = float(m.group(3))
                entry['day_pnl_str']    = m.group(4)
                entry['day_pnl_pct']    = float(m.group(5))
                entry['phase_pnl_str']  = m.group(6)
                entry['phase_pnl_pct']  = float(m.group(7))
            else:
                entry.update({'equity': None, 'cash_pct': None, 'day_pnl_pct': None,
                               'phase_pnl_pct': None, 'day_pnl_str': '—', 'phase_pnl_str': '—'})

            # Positions table
            positions = []
            for line in section.split('\n'):
                if not line.startswith('|'):
                    continue
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if not cells:
                    continue
                if cells[0].lower() in ('ticker', ''):
                    continue
                if re.match(r'^-+$', cells[0]):
                    continue
                if all(c in ('—', '-', '') for c in cells):
                    continue
                if len(cells) >= 7:
                    positions.append({
                        'ticker': cells[0], 'shares': cells[1], 'entry': cells[2],
                        'close': cells[3], 'day_chg': cells[4],
                        'unreal_pnl': cells[5], 'stop': cells[6],
                    })
            entry['positions'] = positions

            # Notes
            m = re.search(r'\*\*Notes:\*\*\s*(.+?)(?=\n\n|\Z)', section, re.DOTALL)
            entry['notes'] = m.group(1).strip() if m else ''

            entries.append(entry)

        if not entries:
            return empty
        return {'latest': entries[-1], 'history': entries[-14:]}
    except Exception:
        return empty


def parse_research_log(path: Path):
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return None

    try:
        clean = strip_fenced(text)
        parts = re.split(r'\n(?=## \d{4}-\d{2}-\d{2})', clean)
        dated = [p.strip() for p in parts if re.match(r'## \d{4}-\d{2}-\d{2}', p.strip())]
        if not dated:
            return None

        latest = dated[-1]

        m = re.match(r'## (\d{4}-\d{2}-\d{2})\s*[—-]+\s*(.+)', latest)
        date_str = m.group(1) if m else ''
        title    = m.group(2).strip() if m else ''

        # Decision
        decision = 'HOLD'
        dec_section = re.search(r'### Decision\s*\n(.+?)(?=###|\Z)', latest, re.DOTALL)
        if dec_section:
            dec_text = dec_section.group(1)
            if re.search(r'\bTRADE\b', dec_text, re.IGNORECASE) and \
               not re.search(r'\bHOLD\b', dec_text, re.IGNORECASE):
                decision = 'TRADE'
            # Decision note: first bold-wrapped sentence
            mn = re.search(r'\*\*(.{10,200}?)\*\*', dec_text)
            decision_note = mn.group(1).strip() if mn else dec_text.strip()[:160]
        else:
            m2 = re.search(r'\bTRADE\b', latest, re.IGNORECASE)
            decision_note = ''
            if m2:
                decision = 'TRADE'

        # Market context bullets
        market_lines = []
        ctx = re.search(r'### (?:Market Context|Key Catalysts)\s*\n(.+?)(?=###|\Z)', latest, re.DOTALL)
        if ctx:
            for line in ctx.group(1).strip().split('\n'):
                line = re.sub(r'^\s*[-*]\s*', '', line).strip()
                if line and len(line) > 8:
                    market_lines.append(line)

        return {
            'date': date_str,
            'title': title,
            'decision': decision,
            'decision_note': decision_note[:160],
            'market_lines': market_lines[:7],
        }
    except Exception:
        return None


def parse_weekly_review(path: Path):
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return None

    try:
        clean = strip_fenced(text)
        if '## Week ending' not in clean:
            return None

        parts = re.split(r'\n(?=## Week ending)', clean)
        week_parts = [p for p in parts if p.strip().startswith('## Week ending')]
        if not week_parts:
            return None

        latest = week_parts[-1]

        m = re.search(r'## Week ending\s+(\S+)', latest)
        week_end = m.group(1) if m else ''

        stats = {}
        for row in re.finditer(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', latest):
            key = row.group(1).strip().lower().replace(' ', '_').replace('&', 'and')
            val = row.group(2).strip()
            if key not in ('metric', '---', '------', 'value'):
                stats[key] = val

        m = re.search(r'Overall Grade:\s*(\w+)', latest)
        grade = m.group(1) if m else stats.get('overall_grade', '—')

        return {'week_end': week_end, 'stats': stats, 'grade': grade}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def pnl_class(v) -> str:
    try:
        text = str(v).replace(',', '')
        m = re.search(r'([+\-]?)\$?\d+(?:\.\d+)?', text)
        if not m:
            return 'neu'
        f = float(m.group(0).replace('$', ''))
        if f > 0:  return 'pos'
        if f < 0:  return 'neg'
    except (ValueError, TypeError):
        pass
    return 'neu'


def fmt_dollar(v, sign=False) -> str:
    try:
        f = float(str(v).replace('$', '').replace(',', '').replace('+', ''))
        pre = '+' if (sign and f > 0) else ''
        return f'{pre}${f:,.2f}'
    except (ValueError, TypeError):
        return '—'


def fmt_pct(v, sign=True) -> str:
    try:
        f = float(str(v).replace('%', '').replace('+', ''))
        pre = '+' if (sign and f > 0) else ''
        return f'{pre}{f:.2f}%'
    except (ValueError, TypeError):
        return '—'


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_positions(positions: list) -> str:
    if not positions:
        return '<div class="no-data">NO OPEN POSITIONS</div>'

    rows = ''
    for p in positions:
        dc = pnl_class(p.get('day_chg', '0'))
        uc = pnl_class(p.get('unreal_pnl', '0'))
        rows += (
            f'<tr>'
            f'<td class="ticker-cell">{p["ticker"]}</td>'
            f'<td class="num">{p["shares"]}</td>'
            f'<td class="num">{p["entry"]}</td>'
            f'<td class="num">{p["close"]}</td>'
            f'<td class="num {dc}">{p["day_chg"]}</td>'
            f'<td class="num {uc}">{p["unreal_pnl"]}</td>'
            f'<td><span class="stop-pill">{p["stop"]}</span></td>'
            f'</tr>'
        )
    return (
        '<div class="table-scroll"><table>'
        '<thead><tr>'
        '<th>Ticker</th><th>Shares</th><th>Entry</th><th>Close/Current</th>'
        '<th>Day Chg</th><th>Unrealized P&L</th><th>Stop</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table></div>'
    )


def build_research(research) -> str:
    if not research:
        return '<div class="no-data">No pre-market research for today yet.</div>'

    decision    = research.get('decision', 'HOLD')
    badge_class = 'badge-trade' if decision == 'TRADE' else 'badge-hold'
    note        = research.get('decision_note', '')
    date_str    = research.get('date', '')
    lines       = research.get('market_lines', [])

    mkt_html = ''.join(f'<div class="mkt-line">{l}</div>' for l in lines) \
               or '<div style="color:#374151;font-size:0.8rem;">No market context found.</div>'

    return (
        f'<div class="research-grid">'
        f'<div>'
        f'<div class="label">Market Context &middot; {date_str}</div>'
        f'{mkt_html}'
        f'</div>'
        f'<div class="decision-box">'
        f'<div class="label">Today\'s Decision</div>'
        f'<span class="{badge_class}">{decision}</span>'
        f'<div style="font-size:0.72rem;color:#6b7280;line-height:1.55;">{note}</div>'
        f'</div>'
        f'</div>'
    )


def build_history(history: list) -> str:
    if not history:
        return '<div class="no-data">No trade log entries yet.</div>'

    rows = ''
    for e in reversed(history):
        dc  = pnl_class(e.get('day_pnl_pct'))
        pc  = pnl_class(e.get('phase_pnl_pct'))
        eq  = fmt_dollar(e.get('equity')) if e.get('equity') is not None else '—'
        dp  = fmt_pct(e.get('day_pnl_pct'))
        pp  = fmt_pct(e.get('phase_pnl_pct'))
        cp  = f"{e.get('cash_pct', 0):.0f}%" if e.get('cash_pct') is not None else '—'
        np_ = len(e.get('positions', []))
        rows += (
            f'<tr>'
            f'<td class="muted-cell">{e.get("date","—")}</td>'
            f'<td class="quiet-cell">{e.get("day_label","—")}</td>'
            f'<td class="num">{eq}</td>'
            f'<td class="num {dc}">{dp}</td>'
            f'<td class="num {pc}">{pp}</td>'
            f'<td class="num quiet-cell">{cp} cash</td>'
            f'<td class="quiet-cell">{np_} pos</td>'
            f'</tr>'
        )
    return (
        '<div class="table-scroll"><table>'
        '<thead><tr>'
        '<th>Date</th><th>Session</th><th>Equity</th><th>Day P&L</th>'
        '<th>Phase P&L</th><th>Cash</th><th>Positions</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table></div>'
    )


def build_weekly(weekly) -> tuple:
    if not weekly:
        return (
            'Weekly Stats',
            '<div class="no-data" style="text-align:left;">No weekly review yet — first review runs Friday at 4 PM CT.</div>'
        )

    stats  = weekly.get('stats', {})
    grade  = weekly.get('grade', '—')
    label  = f'Week ending {weekly.get("week_end","")}'

    display = [
        ('Week Return',    stats.get('week_return', '—')),
        ('vs S&P',         stats.get('bot_vs_s&p', stats.get('bot_vs_sp', '—'))),
        ('Win Rate',       stats.get('win_rate', '—')),
        ('Profit Factor',  stats.get('profit_factor', '—')),
    ]
    chips = ''.join(
        f'<span class="chip">{lbl}: <span class="chip-val">{val}</span></span>'
        for lbl, val in display
    )
    chips += f'<span class="chip">Grade: <span style="color:#f59e0b;font-weight:700;">{grade}</span></span>'

    return label, f'<div class="chips-row">{chips}</div>'


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_html(trade: dict, research, weekly, generated_at: str) -> str:
    latest   = trade.get('latest') or {}
    history  = trade.get('history', [])

    equity       = latest.get('equity')
    cash_pct     = latest.get('cash_pct')
    day_pnl_pct  = latest.get('day_pnl_pct')
    phase_pnl_pct= latest.get('phase_pnl_pct')
    positions    = latest.get('positions', [])

    equity_fmt    = fmt_dollar(equity) if equity is not None else '—'
    cash_pct_fmt  = f'{cash_pct:.1f}%' if cash_pct is not None else '—'
    day_pct_fmt   = fmt_pct(day_pnl_pct)
    phase_pct_fmt = fmt_pct(phase_pnl_pct)
    day_str       = latest.get('day_pnl_str', '—')
    phase_str     = latest.get('phase_pnl_str', '—')
    pos_count     = len(positions)

    day_cls   = pnl_class(day_pnl_pct)
    phase_cls = pnl_class(phase_pnl_pct)
    cash_cls  = 'amb' if (cash_pct or 0) > 50 else 'pos'
    cash_acc  = 'amber' if (cash_pct or 0) > 50 else 'green'
    day_acc   = 'green' if day_cls == 'pos' else ('red' if day_cls == 'neg' else 'gray')

    pos_html     = build_positions(positions)
    research_html= build_research(research)
    hist_html    = build_history(history)
    weekly_label, weekly_html = build_weekly(weekly)

    cash_note = 'idle ↑' if (cash_pct or 0) > 50 else 'deployed'
    n_hist    = len(history)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Trading Bot &middot; Dashboard</title>
  <meta http-equiv="refresh" content="300">
  <style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div class="header-bar">
    <div>
      <div style="display:flex;align-items:center;gap:10px;">
        <span class="brand-kicker">Trading Operations</span>
        <span class="mode-pill">PAPER</span>
      </div>
      <div class="brand-title">Autonomous Trader</div>
    </div>
    <div class="status-line">
      <span class="live-dot"></span>
      <span>Updated {generated_at}</span>
      <span style="color:var(--dim);">&middot;</span>
      <span>auto-refreshes every 5 min</span>
    </div>
  </div>

  <!-- Metric cards -->
  <div class="cards-grid">
    <div class="card metric-card accent-blue">
      <div class="label">Portfolio Equity</div>
      <div class="num metric-value">{equity_fmt}</div>
    </div>
    <div class="card metric-card accent-{day_acc}">
      <div class="label">Day P&amp;L</div>
      <div class="num {day_cls} metric-value">{day_str}</div>
      <div class="num {day_cls} metric-sub">{day_pct_fmt}</div>
    </div>
    <div class="card metric-card accent-purple">
      <div class="label">Phase P&amp;L</div>
      <div class="num {phase_cls} metric-value">{phase_str}</div>
      <div class="num {phase_cls} metric-sub">{phase_pct_fmt}</div>
    </div>
    <div class="card metric-card accent-{cash_acc}">
      <div class="label">Cash</div>
      <div class="num {cash_cls} metric-value">{cash_pct_fmt}</div>
      <div class="metric-sub">{cash_note}</div>
    </div>
    <div class="card metric-card accent-gray">
      <div class="label">Open Positions</div>
      <div class="num metric-value">{pos_count}</div>
      <div class="metric-sub">of 6 max</div>
    </div>
  </div>

  <div class="section-stack">
  <!-- Positions -->
  <div class="card">
    <div class="label">Open Positions</div>
    {pos_html}
  </div>

  <!-- Research -->
  <div class="card">
    <div class="label">Pre-market Research</div>
    {research_html}
  </div>

  <!-- Trade Log -->
  <div class="card">
    <div class="label">Recent Trade Log &middot; last {n_hist} sessions</div>
    {hist_html}
  </div>

  <!-- Weekly stats -->
  <div class="card">
    <div class="label">{weekly_label}</div>
    {weekly_html}
  </div>
  </div>

  <footer>Generated {generated_at} by tools/dashboard.py &middot; auto-deploys via Netlify on every git push</footer>

</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if _TZ:
        now_str = datetime.now(_TZ).strftime('%Y-%m-%d %H:%M CT')
    else:
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    trade    = parse_trade_log(ROOT / 'memory' / 'TRADE-LOG.md')
    research = parse_research_log(ROOT / 'memory' / 'RESEARCH-LOG.md')
    weekly   = parse_weekly_review(ROOT / 'memory' / 'WEEKLY-REVIEW.md')

    docs_dir = ROOT / 'docs'
    docs_dir.mkdir(exist_ok=True)

    html = render_html(trade, research, weekly, now_str)
    (docs_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f'[dashboard] wrote docs/index.html at {now_str}')


if __name__ == '__main__':
    main()
