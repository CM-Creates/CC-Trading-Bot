#!/usr/bin/env python3
"""
Email notification wrapper using Resend API.
Usage: python tools/slack.py "<message>"

Requires RESEND_API_KEY and NOTIFY_EMAIL_TO in env.
Falls back to appending to DAILY-SUMMARY.md if API key is missing.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Load .env if present (local runs)
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

msg_text = sys.argv[1]
email_to = os.environ.get("NOTIFY_EMAIL_TO", "")
api_key = os.environ.get("RESEND_API_KEY", "")
stamp = datetime.now().strftime("%Y-%m-%d %H:%M")


def _fallback():
    fallback = ROOT / "DAILY-SUMMARY.md"
    with fallback.open("a") as f:
        f.write(f"\n---\n## {stamp} (fallback — Resend not configured)\n{msg_text}\n")
    print("[notify fallback] appended to DAILY-SUMMARY.md")
    print(msg_text)


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

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": "Trading Bot <onboarding@resend.dev>",
            "to": [email_to],
            "subject": f"Trading Bot — {stamp}",
            "text": msg_text,
        },
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"[notify] email sent to {email_to} (id: {result.get('id', '?')})")

except Exception as e:
    print(f"WARNING: Resend failed ({e}) — falling back to file", file=sys.stderr)
    _fallback()
