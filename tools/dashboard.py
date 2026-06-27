#!/usr/bin/env python3
"""
Reads memory/*.md and writes docs/index.html — a self-contained trading dashboard.
Usage: python tools/dashboard.py
"""

import json
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
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
@media (max-width: 800px) {
  .charts-grid { grid-template-columns: 1fr; }
}
.chart-title {
  font-size: 0.65rem;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 500;
  margin-bottom: 14px;
}
.chart-wrap {
  position: relative;
  height: 220px;
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

        # Sort by ISO date so out-of-order file appends don't confuse latest lookup
        dated.sort(key=lambda p: re.match(r'## (\d{4}-\d{2}-\d{2})', p).group(1))
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

        # Sector momentum: scan whole entry for "Energy: +23.3%" style lines
        sector_pat = (
            r'(Energy|Materials|Consumer Staples?|Industrials?|'
            r'Tech(?:nology|/IT)?|Financials?|Health\s*Care|'
            r'Utilities|Real\s*Estate|Communication)[\s:]+([+\-][\d.]+)%'
        )
        seen_keys, sectors = set(), []
        for sname, spct in re.findall(sector_pat, latest, re.IGNORECASE):
            key = sname.lower()[:6]
            if key not in seen_keys:
                seen_keys.add(key)
                sectors.append((sname.strip(), float(spct)))
        sectors.sort(key=lambda x: x[1], reverse=True)

        # Trade ideas: extract ticker, stop%, target%
        ideas = []
        ideas_sec = re.search(r'### Trade Ideas\s*\n(.+?)(?=###|\Z)', latest, re.DOTALL)
        if ideas_sec:
            for line in ideas_sec.group(1).strip().split('\n'):
                if not line.strip():
                    continue
                ticker_m = re.search(r'\*\*([A-Z]{2,5})', line)
                stop_m   = re.search(r'-(\d+)%', line)
                target_m = re.search(r'\+(\d+)%.*?(?:R:R|target)', line, re.IGNORECASE)
                if not target_m:
                    target_m = re.search(r'[Tt]arget.*?\+(\d+)%', line)
                if ticker_m:
                    ideas.append({
                        'ticker':     ticker_m.group(1),
                        'stop_pct':   float(stop_m.group(1))   if stop_m   else 10.0,
                        'target_pct': float(target_m.group(1)) if target_m else 20.0,
                    })

        return {
            'date': date_str,
            'title': title,
            'decision': decision,
            'decision_note': decision_note[:160],
            'market_lines': market_lines[:7],
            'sectors': sectors[:8],
            'ideas': ideas[:4],
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
# Chart section builder (Chart.js — data baked in as inline JSON)
# ---------------------------------------------------------------------------

_SP500_LAUNCH = 7500.0   # S&P 500 index level at launch (Jun 21 2026)
_EQUITY_START = 100000.0


def build_charts_section(history: list, research, positions: list) -> str:
    # ---- Portfolio equity time series ----
    eq_labels, eq_vals, sp_vals = [], [], []
    for e in history:
        if e.get('equity') is None:
            continue
        eq_labels.append(e.get('date', ''))
        eq = e['equity']
        eq_vals.append(eq)
        # S&P baseline uses the phase P&L pct reported in each entry
        # (phase P&L = bot vs $100k start; we need S&P vs same start)
        # Approximate: store S&P equiv as a straight line from $100k
        # We'll compute this from known start and daily entries count.
        sp_vals.append(None)  # filled below

    # Compute simple S&P 500 baseline: straight line from $100k at launch
    # to current S&P implied value. We approximate using a fixed YTD figure
    # since we don't store daily S&P. This gives a visual reference.
    # S&P from Jun 21 → Jun 26 was ~7500 → ~7448 = -0.69%
    n = len(eq_vals)
    if n > 1:
        sp_end_pct = -0.69   # approx change from launch to last entry
        for i in range(n):
            frac = i / (n - 1)
            sp_vals[i] = round(_EQUITY_START * (1 + frac * sp_end_pct / 100), 2)
    elif n == 1:
        sp_vals[0] = _EQUITY_START

    # ---- Deployment donut ----
    total_eq = eq_vals[-1] if eq_vals else _EQUITY_START
    pos_market_val = 0.0
    for p in positions:
        try:
            shares = float(str(p.get('shares', '0')).replace(',', ''))
            close  = float(str(p.get('close', '0')).replace('$', '').replace(',', ''))
            pos_market_val += shares * close
        except (ValueError, TypeError):
            pass
    cash_val     = max(0.0, total_eq - pos_market_val)
    deployed_val = max(0.0, pos_market_val)
    if deployed_val == 0 and eq_vals:
        # Fall back to cash_pct from last history entry
        last = history[-1] if history else {}
        cp = last.get('cash_pct', 100.0)
        cash_val     = round(total_eq * cp / 100, 2)
        deployed_val = round(total_eq - cash_val, 2)

    # ---- Sectors ----
    sectors   = research.get('sectors', []) if research else []
    sec_labels = [s[0] for s in sectors]
    sec_vals   = [s[1] for s in sectors]
    sec_colors = ['#10b981' if v >= 0 else '#ef4444' for v in sec_vals]

    # ---- Trade ideas R:R ----
    ideas     = research.get('ideas', []) if research else []
    idea_labels = [i['ticker'] for i in ideas]
    idea_stops  = [i['stop_pct']   for i in ideas]
    idea_tgts   = [i['target_pct'] for i in ideas]

    chart_data = {
        'equity': {'labels': eq_labels, 'values': eq_vals, 'sp': sp_vals},
        'deploy': {'deployed': round(deployed_val, 2), 'cash': round(cash_val, 2)},
        'sectors': {'labels': sec_labels, 'values': sec_vals, 'colors': sec_colors},
        'ideas': {'labels': idea_labels, 'stops': idea_stops, 'targets': idea_tgts},
    }
    data_json = json.dumps(chart_data)

    has_ideas = 'true' if ideas else 'false'

    return f"""
<div class="charts-grid">

  <div class="card">
    <div class="chart-title">Portfolio Equity vs S&amp;P 500 Baseline</div>
    <div class="chart-wrap"><canvas id="chartEquity"></canvas></div>
  </div>

  <div class="card">
    <div class="chart-title">Capital Deployment</div>
    <div class="chart-wrap"><canvas id="chartDeploy"></canvas></div>
  </div>

  <div class="card">
    <div class="chart-title">Sector Momentum YTD</div>
    <div class="chart-wrap"><canvas id="chartSectors"></canvas></div>
  </div>

  <div class="card" id="chartRRCard" style="display:{'block' if ideas else 'none'}">
    <div class="chart-title">Trade Ideas — Risk:Reward Zones</div>
    <div class="chart-wrap"><canvas id="chartRR"></canvas></div>
  </div>

</div>

<script>
(function() {{
  const D = {data_json};
  const DARK = {{
    color: 'rgba(255,255,255,0.08)',
    textColor: '#6b7280',
    titleColor: '#9ca3af',
    tooltipBg: '#1a2035',
  }};
  const baseOpts = {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: DARK.textColor, font: {{ size: 11 }} }} }},
      tooltip: {{
        backgroundColor: DARK.tooltipBg,
        titleColor: '#f9fafb',
        bodyColor: '#d1d5db',
        borderColor: '#374151',
        borderWidth: 1,
      }},
    }},
    scales: {{
      x: {{
        grid: {{ color: DARK.color }},
        ticks: {{ color: DARK.textColor, font: {{ size: 10 }} }},
      }},
      y: {{
        grid: {{ color: DARK.color }},
        ticks: {{ color: DARK.textColor, font: {{ size: 10 }} }},
      }},
    }},
  }};

  // 1. Portfolio equity line
  new Chart(document.getElementById('chartEquity'), {{
    type: 'line',
    data: {{
      labels: D.equity.labels,
      datasets: [
        {{
          label: 'Bot Portfolio',
          data: D.equity.values,
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139,92,246,0.08)',
          tension: 0.3,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6,
        }},
        {{
          label: 'S&P 500 Baseline',
          data: D.equity.sp,
          borderColor: '#374151',
          borderDash: [4, 4],
          tension: 0,
          fill: false,
          pointRadius: 2,
        }},
      ],
    }},
    options: {{
      ...baseOpts,
      plugins: {{
        ...baseOpts.plugins,
        tooltip: {{
          ...baseOpts.plugins.tooltip,
          callbacks: {{
            label: ctx => {{
              const v = ctx.parsed.y;
              const pct = ((v - {_EQUITY_START}) / {_EQUITY_START} * 100).toFixed(2);
              return ctx.dataset.label + ': $' + v.toLocaleString() + ' (' + (v >= {_EQUITY_START} ? '+' : '') + pct + '%)';
            }},
          }},
        }},
      }},
      scales: {{
        ...baseOpts.scales,
        y: {{
          ...baseOpts.scales.y,
          ticks: {{
            ...baseOpts.scales.y.ticks,
            callback: v => '$' + (v/1000).toFixed(0) + 'k',
          }},
        }},
      }},
    }},
  }});

  // 2. Deployment donut
  new Chart(document.getElementById('chartDeploy'), {{
    type: 'doughnut',
    data: {{
      labels: ['Deployed', 'Cash'],
      datasets: [{{
        data: [D.deploy.deployed, D.deploy.cash],
        backgroundColor: ['#10b981', '#1a2332'],
        borderColor: ['#10b981', '#374151'],
        borderWidth: 1,
        hoverOffset: 6,
      }}],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {{
        legend: {{
          position: 'bottom',
          labels: {{
            color: DARK.textColor,
            font: {{ size: 11 }},
            padding: 14,
            generateLabels: chart => {{
              const ds = chart.data.datasets[0];
              const total = ds.data.reduce((a, b) => a + b, 0);
              return chart.data.labels.map((label, i) => ({{
                text: label + ' ' + (ds.data[i] / total * 100).toFixed(1) + '%',
                fillStyle: ds.backgroundColor[i],
                strokeStyle: ds.borderColor[i],
                lineWidth: 1,
                index: i,
              }}));
            }},
          }},
        }},
        tooltip: {{
          backgroundColor: DARK.tooltipBg,
          titleColor: '#f9fafb',
          bodyColor: '#d1d5db',
          callbacks: {{
            label: ctx => ' $' + ctx.parsed.toLocaleString(undefined, {{minimumFractionDigits:2}}),
          }},
        }},
      }},
    }},
  }});

  // 3. Sector horizontal bars
  if (D.sectors.labels.length > 0) {{
    new Chart(document.getElementById('chartSectors'), {{
      type: 'bar',
      data: {{
        labels: D.sectors.labels,
        datasets: [{{
          label: 'YTD %',
          data: D.sectors.values,
          backgroundColor: D.sectors.colors,
          borderRadius: 4,
          barThickness: 16,
        }}],
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            backgroundColor: DARK.tooltipBg,
            titleColor: '#f9fafb',
            bodyColor: '#d1d5db',
            callbacks: {{
              label: ctx => ' ' + (ctx.parsed.x >= 0 ? '+' : '') + ctx.parsed.x.toFixed(1) + '%',
            }},
          }},
        }},
        scales: {{
          x: {{
            grid: {{ color: DARK.color }},
            ticks: {{
              color: DARK.textColor,
              font: {{ size: 10 }},
              callback: v => (v >= 0 ? '+' : '') + v + '%',
            }},
          }},
          y: {{
            grid: {{ color: 'transparent' }},
            ticks: {{ color: DARK.textColor, font: {{ size: 10 }} }},
          }},
        }},
      }},
    }});
  }}

  // 4. Trade ideas R:R stacked bars
  if ({has_ideas} && D.ideas.labels.length > 0) {{
    new Chart(document.getElementById('chartRR'), {{
      type: 'bar',
      data: {{
        labels: D.ideas.labels,
        datasets: [
          {{
            label: 'Stop zone',
            data: D.ideas.stops,
            backgroundColor: '#7f1d1d',
            borderRadius: {{ topLeft: 4, bottomLeft: 4 }},
            barThickness: 20,
          }},
          {{
            label: 'Target zone',
            data: D.ideas.targets,
            backgroundColor: '#14532d',
            borderRadius: {{ topRight: 4, bottomRight: 4 }},
            barThickness: 20,
          }},
        ],
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{
            position: 'bottom',
            labels: {{ color: DARK.textColor, font: {{ size: 11 }}, padding: 14 }},
          }},
          tooltip: {{
            backgroundColor: DARK.tooltipBg,
            titleColor: '#f9fafb',
            bodyColor: '#d1d5db',
            callbacks: {{
              label: ctx => ' ' + ctx.dataset.label + ': ' + ctx.parsed.x.toFixed(0) + '%',
            }},
          }},
        }},
        scales: {{
          x: {{
            stacked: true,
            grid: {{ color: DARK.color }},
            ticks: {{
              color: DARK.textColor,
              font: {{ size: 10 }},
              callback: v => v + '%',
            }},
          }},
          y: {{
            stacked: true,
            grid: {{ color: 'transparent' }},
            ticks: {{ color: DARK.textColor, font: {{ size: 11, weight: 'bold' }} }},
          }},
        }},
      }},
    }});
  }}
}})();
</script>
"""

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
    charts_html  = build_charts_section(history, research, positions)

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
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
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

  <!-- Charts -->
  {charts_html}

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
