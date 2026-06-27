#!/usr/bin/env python3
"""
Email notification wrapper using Resend API.
Usage: python tools/slack.py "<message>"

Requires RESEND_API_KEY and NOTIFY_EMAIL_TO in env.
Falls back to appending to DAILY-SUMMARY.md if API key is missing.
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

if len(sys.argv) < 2 or not sys.argv[1].strip():
    print('Usage: python tools/slack.py "<message>"', file=sys.stderr)
    sys.exit(1)

# Fix literal \n sequences that come from shell arg quoting
msg_text      = sys.argv[1].replace('\\n', '\n')
email_to      = os.environ.get("NOTIFY_EMAIL_TO", "")
api_key       = os.environ.get("RESEND_API_KEY", "")
dashboard_url = os.environ.get("DASHBOARD_URL", "")
stamp         = datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _fallback():
    fallback = ROOT / "DAILY-SUMMARY.md"
    with fallback.open("a") as f:
        f.write(f"\n---\n## {stamp} (fallback — Resend not configured)\n{msg_text}\n")
    print("[notify fallback] appended to DAILY-SUMMARY.md")
    print(msg_text)


# ---------------------------------------------------------------------------
# Data extraction from memory files (lightweight regex, no dashboard parsers)
# ---------------------------------------------------------------------------

def _read_latest_tradelog():
    """Return latest EOD metrics dict from TRADE-LOG.md, or None."""
    try:
        text = (ROOT / "memory" / "TRADE-LOG.md").read_text(encoding="utf-8")
        pattern = (
            r'\*\*Portfolio:\*\*\s*\$([\d,]+\.?\d*)\s*\|'
            r'.*?\*\*Cash:\*\*\s*\$([\d,]+\.?\d*)\s*\(([\d.]+)%\)'
            r'.*?\*\*Day P&L:\*\*\s*([+\-]?\$[\d,.]+)\s*\(([+\-]?[\d.]+)%\)'
            r'.*?\*\*Phase P&L:\*\*\s*([+\-]?\$[\d,.]+)\s*\(([+\-]?[\d.]+)%\)'
        )
        matches = list(re.finditer(pattern, text))
        if not matches:
            return None
        m = matches[-1]
        return {
            'equity':        float(m.group(1).replace(',', '')),
            'cash_pct':      float(m.group(3)),
            'day_pnl_str':   m.group(4),
            'day_pnl_pct':   float(m.group(5)),
            'phase_pnl_str': m.group(6),
            'phase_pnl_pct': float(m.group(7)),
        }
    except Exception:
        return None


def _read_latest_research():
    """Return decision, sectors list, and trade ideas from latest RESEARCH-LOG entry."""
    try:
        text = (ROOT / "memory" / "RESEARCH-LOG.md").read_text(encoding="utf-8")
        parts = re.split(r'\n(?=## \d{4}-\d{2}-\d{2})', text)
        dated = [p.strip() for p in parts if re.match(r'## \d{4}-\d{2}-\d{2}', p.strip())]
        if not dated:
            return None
        dated.sort(key=lambda p: re.match(r'## (\d{4}-\d{2}-\d{2})', p).group(1))
        latest = dated[-1]

        # Decision + note
        decision = 'HOLD'
        dec_note = ''
        dec_sec = re.search(r'### Decision\s*\n(.+?)(?=###|\Z)', latest, re.DOTALL)
        if dec_sec:
            dec_text = dec_sec.group(1)
            if re.search(r'\bTRADE\b', dec_text, re.IGNORECASE) and \
               not re.search(r'^HOLD\b', dec_text.strip(), re.IGNORECASE):
                decision = 'TRADE'
            mn = re.search(r'\*\*(.{10,200}?)\*\*', dec_text)
            dec_note = mn.group(1).strip() if mn else dec_text.strip()[:160]

        # Sectors: scan whole entry for "Energy: +23.3%" style lines
        sector_pat = (
            r'(Energy|Materials|Consumer Staples?|Industrials?|'
            r'Tech(?:nology|/IT)?|Financials?|Health\s*Care|'
            r'Utilities|Real\s*Estate|Communication)[\s:]+([+\-][\d.]+)%'
        )
        seen_keys, sectors = set(), []
        for name, pct_str in re.findall(sector_pat, latest, re.IGNORECASE):
            key = name.lower()[:6]
            if key not in seen_keys:
                seen_keys.add(key)
                sectors.append((name.strip(), float(pct_str)))
        sectors.sort(key=lambda x: x[1], reverse=True)
        sectors = sectors[:8]

        # Trade ideas: extract ticker, stop%, target%
        ideas = []
        ideas_sec = re.search(r'### Trade Ideas\s*\n(.+?)(?=###|\Z)', latest, re.DOTALL)
        if ideas_sec:
            for line in ideas_sec.group(1).strip().split('\n'):
                if not line.strip():
                    continue
                ticker_m = re.search(r'\*\*([A-Z]{2,5})', line)
                stop_m   = re.search(r'-(\d+)%', line)
                # look for target % before or after "R:R" / "target" keyword
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
            'decision':      decision,
            'decision_note': dec_note[:200],
            'sectors':       sectors,
            'ideas':         ideas[:3],
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# HTML email builder
# ---------------------------------------------------------------------------

def _pc(v):
    """Return green / red / gray hex for numeric sign."""
    if v > 0:  return '#10b981'
    if v < 0:  return '#ef4444'
    return '#6b7280'


def render_email_html(msg, trade, research):
    # ---- Metrics ----
    equity        = trade['equity']        if trade else None
    cash_pct      = trade['cash_pct']      if trade else None
    day_pnl_pct   = trade['day_pnl_pct']   if trade else 0.0
    day_pnl_str   = trade['day_pnl_str']   if trade else '—'
    phase_pnl_pct = trade['phase_pnl_pct'] if trade else 0.0
    phase_pnl_str = trade['phase_pnl_str'] if trade else '—'

    deployed_pct = max(0.0, 100.0 - (cash_pct or 100.0))
    eq_fmt   = f'${equity:,.2f}' if equity is not None else '—'
    cash_fmt = f'{cash_pct:.1f}%' if cash_pct is not None else '—'

    day_sign  = '+' if day_pnl_pct > 0 else ''
    ph_sign   = '+' if phase_pnl_pct > 0 else ''
    day_fmt   = f'{day_pnl_str} ({day_sign}{day_pnl_pct:.2f}%)'   if trade else '—'
    phase_fmt = f'{phase_pnl_str} ({ph_sign}{phase_pnl_pct:.2f}%)' if trade else '—'
    day_col   = _pc(day_pnl_pct)
    phase_col = _pc(phase_pnl_pct)

    # ---- Decision ----
    decision      = research.get('decision', 'HOLD')  if research else 'HOLD'
    decision_note = research.get('decision_note', '') if research else ''
    dec_color = '#10b981' if decision == 'TRADE' else '#f59e0b'
    dec_bg    = '#0d2b1e' if decision == 'TRADE' else '#2b1d0a'

    # ---- Deployment bar ----
    dep_pct  = round(deployed_pct)
    cash_rem = 100 - dep_pct
    dep_bar = (
        f'<table width="100%" cellspacing="0" cellpadding="0" style="border-radius:5px;overflow:hidden;">'
        f'<tr>'
        f'<td style="background:#10b981;width:{dep_pct}%;height:14px;"></td>'
        f'<td style="background:#1a2332;width:{cash_rem}%;height:14px;"></td>'
        f'</tr></table>'
        f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-top:5px;">'
        f'<tr>'
        f'<td style="font-size:10px;color:#10b981;">&#9646; Deployed {dep_pct}%</td>'
        f'<td align="right" style="font-size:10px;color:#4b5563;">Cash {cash_fmt}</td>'
        f'</tr></table>'
    )

    # ---- Sector bars ----
    sectors = research.get('sectors', []) if research else []
    sector_rows = ''
    if sectors:
        max_abs = max(abs(p) for _, p in sectors) or 1.0
        for name, pct in sectors:
            bcolor = '#10b981' if pct >= 0 else '#ef4444'
            bw = max(4, round(abs(pct) / max_abs * 100))
            sign = '+' if pct > 0 else ''
            sector_rows += (
                f'<tr>'
                f'<td style="font-size:10px;color:#9ca3af;padding:3px 0;'
                f'width:115px;white-space:nowrap;">{name}</td>'
                f'<td style="padding:3px 6px;">'
                f'<div style="background:{bcolor};height:9px;width:{bw}px;'
                f'border-radius:3px;min-width:4px;"></div>'
                f'</td>'
                f'<td style="font-size:10px;color:{bcolor};font-family:monospace;'
                f'white-space:nowrap;">{sign}{pct:.1f}%</td>'
                f'</tr>'
            )
    sector_html = (
        f'<table cellspacing="0" cellpadding="0">{sector_rows}</table>'
        if sector_rows
        else '<div style="font-size:10px;color:#4b5563;">No sector data in today\'s research.</div>'
    )

    # ---- R:R visual (only when TRADE decision and ideas exist) ----
    ideas = research.get('ideas', []) if research else []
    rr_section = ''
    if ideas and decision == 'TRADE':
        rr_rows = ''
        for idea in ideas:
            sp = idea['stop_pct']
            tp = idea['target_pct']
            total = sp + tp or 1.0
            sw = max(4, round(sp / total * 160))
            tw = max(4, round(tp / total * 160))
            rr_rows += (
                f'<tr>'
                f'<td style="font-size:10px;color:#9ca3af;width:46px;'
                f'padding:4px 8px 4px 0;font-family:monospace;">{idea["ticker"]}</td>'
                f'<td>'
                f'<table cellspacing="0" cellpadding="0"><tr>'
                f'<td style="background:#7f1d1d;width:{sw}px;height:13px;'
                f'border-radius:3px 0 0 3px;"></td>'
                f'<td style="background:#14532d;width:{tw}px;height:13px;'
                f'border-radius:0 3px 3px 0;"></td>'
                f'</tr></table>'
                f'</td>'
                f'<td style="font-size:10px;color:#6b7280;padding-left:8px;white-space:nowrap;">'
                f'-{sp:.0f}% / +{tp:.0f}% &middot; {tp/sp:.1f}:1'
                f'</td>'
                f'</tr>'
            )
        rr_section = (
            f'<div style="margin-top:16px;">'
            f'<div style="font-size:9px;color:#4b5563;text-transform:uppercase;'
            f'letter-spacing:0.1em;margin-bottom:8px;">Trade Ideas &mdash; Risk:Reward Zones</div>'
            f'<table cellspacing="0" cellpadding="0">{rr_rows}</table>'
            f'<div style="font-size:9px;color:#374151;margin-top:6px;">'
            f'<span style="display:inline-block;background:#7f1d1d;width:9px;height:7px;'
            f'border-radius:2px;vertical-align:middle;"></span>&nbsp;Stop zone&nbsp;&nbsp;&nbsp;'
            f'<span style="display:inline-block;background:#14532d;width:9px;height:7px;'
            f'border-radius:2px;vertical-align:middle;"></span>&nbsp;Target zone'
            f'</div>'
            f'</div>'
        )

    # ---- Dashboard CTA button ----
    dash_btn = ''
    if dashboard_url:
        dash_btn = (
            f'<tr><td style="padding:14px 0;" align="center">'
            f'<a href="{dashboard_url}" style="background:#8b5cf6;color:#ffffff;'
            f'text-decoration:none;padding:11px 26px;border-radius:8px;font-size:13px;'
            f'font-weight:600;letter-spacing:0.04em;display:inline-block;">'
            f'View Live Dashboard &rarr;'
            f'</a></td></tr>'
        )

    # ---- Message body ----
    body_html = msg.replace('\n', '<br>')

    # ---- Assemble ----
    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '</head>'
        '<body style="margin:0;padding:0;background:#0a0e17;'
        'font-family:system-ui,-apple-system,sans-serif;">'
        '<table width="100%" cellspacing="0" cellpadding="0" style="background:#0a0e17;">'
        '<tr><td align="center" style="padding:20px 12px;">'
        '<table width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%;">'

        # Header
        '<tr><td style="background:#111827;border:1px solid #1f2937;'
        'border-radius:12px 12px 0 0;padding:14px 18px;">'
        '<table width="100%" cellspacing="0" cellpadding="0"><tr>'
        '<td style="font-size:13px;font-weight:700;color:#f9fafb;letter-spacing:0.06em;">'
        'AUTONOMOUS TRADER'
        '<span style="background:#1a2332;color:#6b7280;border-radius:4px;padding:2px 7px;'
        'font-size:9px;margin-left:7px;letter-spacing:0.08em;">PAPER</span>'
        '</td>'
        f'<td align="right" style="font-size:10px;color:#4b5563;">{stamp}</td>'
        '</tr></table>'
        '</td></tr>'

        # Metric cards (4 columns)
        '<tr><td style="padding:2px 0;">'
        '<table width="100%" cellspacing="2" cellpadding="0"><tr>'

        f'<td width="25%" style="background:#111827;border:1px solid #1f2937;'
        f'border-top:2px solid #3b82f6;border-radius:8px;padding:11px;">'
        f'<div style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:4px;">Equity</div>'
        f'<div style="font-size:15px;font-weight:700;color:#f9fafb;font-family:monospace;">{eq_fmt}</div>'
        f'</td>'

        f'<td width="25%" style="background:#111827;border:1px solid #1f2937;'
        f'border-top:2px solid {day_col};border-radius:8px;padding:11px;">'
        f'<div style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:4px;">Day P&amp;L</div>'
        f'<div style="font-size:11px;font-weight:700;color:{day_col};font-family:monospace;">{day_fmt}</div>'
        f'</td>'

        f'<td width="25%" style="background:#111827;border:1px solid #1f2937;'
        f'border-top:2px solid #8b5cf6;border-radius:8px;padding:11px;">'
        f'<div style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:4px;">Phase P&amp;L</div>'
        f'<div style="font-size:11px;font-weight:700;color:{phase_col};font-family:monospace;">{phase_fmt}</div>'
        f'</td>'

        f'<td width="25%" style="background:#111827;border:1px solid #1f2937;'
        f'border-top:2px solid #f59e0b;border-radius:8px;padding:11px;">'
        f'<div style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:4px;">Cash</div>'
        f'<div style="font-size:15px;font-weight:700;color:#f59e0b;font-family:monospace;">{cash_fmt}</div>'
        f'</td>'

        '</tr></table>'
        '</td></tr>'

        # Decision badge
        f'<tr><td style="background:{dec_bg};border:1px solid {dec_color}44;'
        f'border-radius:8px;padding:13px 16px;">'
        f'<table width="100%" cellspacing="0" cellpadding="0">'
        f'<tr><td colspan="2" style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        f'letter-spacing:0.1em;padding-bottom:6px;">Today\'s Decision</td></tr>'
        f'<tr>'
        f'<td style="vertical-align:top;width:85px;">'
        f'<span style="background:{dec_color}22;color:{dec_color};border:1px solid {dec_color}44;'
        f'border-radius:6px;padding:5px 13px;font-size:11px;font-weight:700;'
        f'letter-spacing:0.1em;display:inline-block;">{decision}</span>'
        f'</td>'
        f'<td style="font-size:10px;color:#9ca3af;line-height:1.55;vertical-align:top;">'
        f'{decision_note}'
        f'</td>'
        f'</tr></table>'
        f'</td></tr>'

        # Charts section
        '<tr><td style="background:#111827;border:1px solid #1f2937;'
        'border-radius:8px;padding:14px 16px;">'

        '<div style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        'letter-spacing:0.1em;margin-bottom:8px;">Capital Deployment</div>'
        + dep_bar +

        '<div style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        'letter-spacing:0.1em;margin-top:14px;margin-bottom:8px;">Sector Momentum YTD</div>'
        + sector_html +

        rr_section +

        '</td></tr>'

        # Message body
        '<tr><td style="background:#111827;border:1px solid #1f2937;'
        'border-radius:8px;padding:14px 16px;">'
        '<div style="font-size:8px;color:#4b5563;text-transform:uppercase;'
        'letter-spacing:0.1em;margin-bottom:8px;">Notification</div>'
        '<div style="font-size:12px;color:#d1d5db;line-height:1.75;font-family:monospace;">'
        + body_html +
        '</div>'
        '</td></tr>'

        # Dashboard button
        + dash_btn +

        # Footer
        f'<tr><td style="padding:10px 0;" align="center">'
        f'<div style="font-size:9px;color:#374151;">'
        f'Autonomous Trader &middot; Paper Account &middot; {stamp}'
        f'</div></td></tr>'

        '</table>'
        '</td></tr></table>'
        '</body></html>'
    )


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------

if not api_key:
    print("WARNING: RESEND_API_KEY not set — falling back to file", file=sys.stderr)
    _fallback()
    sys.exit(0)

if not email_to:
    print("WARNING: NOTIFY_EMAIL_TO not set — falling back to file", file=sys.stderr)
    _fallback()
    sys.exit(0)

try:
    import warnings
    import requests
    warnings.filterwarnings("ignore")

    trade    = _read_latest_tradelog()
    research = _read_latest_research()
    html     = render_email_html(msg_text, trade, research)

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": "Trading Bot <onboarding@resend.dev>",
            "to": [email_to],
            "subject": f"Trading Bot — {stamp}",
            "html": html,
            "text": msg_text,
        },
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"[notify] email sent to {email_to} (id: {result.get('id', '?')})")

except Exception as e:
    print(f"WARNING: Resend failed ({e}) — falling back to file", file=sys.stderr)
    _fallback()
