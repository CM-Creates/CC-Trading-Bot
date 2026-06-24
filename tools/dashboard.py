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
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0a0e17;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #f9fafb;
  min-height: 100vh;
}
.wrap { max-width: 1340px; margin: 0 auto; padding: 24px 20px; }
.card {
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 12px;
  padding: 20px;
}
.accent-blue   { border-top: 2px solid #3b82f6; }
.accent-green  { border-top: 2px solid #10b981; }
.accent-red    { border-top: 2px solid #ef4444; }
.accent-purple { border-top: 2px solid #8b5cf6; }
.accent-amber  { border-top: 2px solid #f59e0b; }
.accent-gray   { border-top: 2px solid #374151; }
.badge-trade {
  background: rgba(16,185,129,0.12);
  color: #10b981;
  border: 1px solid rgba(16,185,129,0.3);
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 1rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  display: inline-block;
  font-weight: 700;
}
.badge-hold {
  background: rgba(245,158,11,0.12);
  color: #f59e0b;
  border: 1px solid rgba(245,158,11,0.3);
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 1rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  display: inline-block;
  font-weight: 700;
}
.num { font-family: 'Courier New', monospace; }
.pos { color: #10b981; }
.neg { color: #ef4444; }
.neu { color: #6b7280; }
.amb { color: #f59e0b; }
.label {
  font-size: 0.65rem;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 500;
  margin-bottom: 12px;
}
.live-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  margin-right: 6px;
  animation: pulse 2.5s infinite;
  vertical-align: middle;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.15; }
}
.cards-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
@media (max-width: 900px) {
  .cards-grid { grid-template-columns: repeat(2, 1fr); }
}
table { border-collapse: collapse; width: 100%; }
th {
  border-bottom: 1px solid #1f2937;
  padding: 10px 14px;
  text-align: left;
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #4b5563;
  font-weight: 500;
}
td {
  border-bottom: 1px solid #111827;
  padding: 10px 14px;
  font-size: 0.875rem;
  color: #d1d5db;
}
tr:hover td { background: rgba(255,255,255,0.025); }
.stop-pill {
  background: rgba(99,102,241,0.12);
  color: #818cf8;
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.72rem;
  font-family: 'Courier New', monospace;
}
.research-grid {
  display: grid;
  grid-template-columns: 1fr 220px;
  gap: 20px;
}
@media (max-width: 700px) {
  .research-grid { grid-template-columns: 1fr; }
}
.mkt-line {
  padding: 7px 0;
  border-bottom: 1px solid #1a2332;
  font-size: 0.8rem;
  color: #9ca3af;
  line-height: 1.5;
}
.mkt-line:last-child { border-bottom: none; }
.decision-box {
  background: #0a0e17;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 12px;
}
.chip {
  background: #1a2332;
  color: #9ca3af;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 0.78rem;
  white-space: nowrap;
  display: inline-block;
}
.chip-val { color: #f9fafb; font-family: 'Courier New', monospace; }
.chips-row { display: flex; flex-wrap: wrap; gap: 10px; padding: 4px 0; }
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #1f2937;
}
.no-data {
  text-align: center;
  padding: 28px 0;
  color: #374151;
  font-size: 0.85rem;
  letter-spacing: 0.05em;
}
footer {
  text-align: center;
  font-size: 0.68rem;
  color: #1f2937;
  padding: 12px 0 4px;
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
        f = float(str(v).replace('%', '').replace('+', '').replace('$', '').replace(',', ''))
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
            f'<td style="font-weight:700;color:#f9fafb;">{p["ticker"]}</td>'
            f'<td class="num">{p["shares"]}</td>'
            f'<td class="num">{p["entry"]}</td>'
            f'<td class="num">{p["close"]}</td>'
            f'<td class="num {dc}">{p["day_chg"]}</td>'
            f'<td class="num {uc}">{p["unreal_pnl"]}</td>'
            f'<td><span class="stop-pill">{p["stop"]}</span></td>'
            f'</tr>'
        )
    return (
        '<table>'
        '<thead><tr>'
        '<th>Ticker</th><th>Shares</th><th>Entry</th><th>Close/Current</th>'
        '<th>Day Chg</th><th>Unrealized P&L</th><th>Stop</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
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
            f'<td style="color:#9ca3af;">{e.get("date","—")}</td>'
            f'<td style="color:#4b5563;font-size:0.75rem;">{e.get("day_label","—")}</td>'
            f'<td class="num">{eq}</td>'
            f'<td class="num {dc}">{dp}</td>'
            f'<td class="num {pc}">{pp}</td>'
            f'<td class="num" style="color:#4b5563;">{cp} cash</td>'
            f'<td style="color:#4b5563;font-size:0.75rem;">{np_} pos</td>'
            f'</tr>'
        )
    return (
        '<table>'
        '<thead><tr>'
        '<th>Date</th><th>Session</th><th>Equity</th><th>Day P&L</th>'
        '<th>Phase P&L</th><th>Cash</th><th>Positions</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
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
    <div style="display:flex;align-items:center;gap:14px;">
      <span style="font-size:1.05rem;font-weight:700;letter-spacing:0.06em;">AUTONOMOUS TRADER</span>
      <span style="background:#1a2332;color:#4b5563;border-radius:4px;padding:3px 9px;font-size:0.65rem;letter-spacing:0.1em;font-weight:600;">PAPER</span>
    </div>
    <div style="font-size:0.75rem;color:#4b5563;display:flex;align-items:center;gap:6px;">
      <span class="live-dot"></span>
      <span>Updated {generated_at}</span>
      <span style="color:#1f2937;">&middot;</span>
      <span style="color:#374151;">auto-refreshes every 5 min</span>
    </div>
  </div>

  <!-- Metric cards -->
  <div class="cards-grid">
    <div class="card accent-blue">
      <div class="label">Portfolio Equity</div>
      <div class="num" style="font-size:1.55rem;font-weight:700;">{equity_fmt}</div>
    </div>
    <div class="card accent-{day_acc}">
      <div class="label">Day P&amp;L</div>
      <div class="num {day_cls}" style="font-size:1.4rem;font-weight:700;">{day_str}</div>
      <div class="num {day_cls}" style="font-size:0.82rem;margin-top:5px;">{day_pct_fmt}</div>
    </div>
    <div class="card accent-purple">
      <div class="label">Phase P&amp;L</div>
      <div class="num {phase_cls}" style="font-size:1.4rem;font-weight:700;">{phase_str}</div>
      <div class="num {phase_cls}" style="font-size:0.82rem;margin-top:5px;">{phase_pct_fmt}</div>
    </div>
    <div class="card accent-{cash_acc}">
      <div class="label">Cash</div>
      <div class="num {cash_cls}" style="font-size:1.55rem;font-weight:700;">{cash_pct_fmt}</div>
      <div style="font-size:0.72rem;color:#4b5563;margin-top:5px;">{cash_note}</div>
    </div>
    <div class="card accent-gray">
      <div class="label">Open Positions</div>
      <div class="num" style="font-size:1.55rem;font-weight:700;color:#f9fafb;">{pos_count}</div>
      <div style="font-size:0.72rem;color:#4b5563;margin-top:5px;">of 6 max</div>
    </div>
  </div>

  <!-- Positions -->
  <div class="card" style="margin-bottom:16px;">
    <div class="label">Open Positions</div>
    {pos_html}
  </div>

  <!-- Research -->
  <div class="card" style="margin-bottom:16px;">
    <div class="label">Pre-market Research</div>
    {research_html}
  </div>

  <!-- Trade Log -->
  <div class="card" style="margin-bottom:16px;">
    <div class="label">Recent Trade Log &middot; last {n_hist} sessions</div>
    {hist_html}
  </div>

  <!-- Weekly stats -->
  <div class="card" style="margin-bottom:8px;">
    <div class="label">{weekly_label}</div>
    {weekly_html}
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
