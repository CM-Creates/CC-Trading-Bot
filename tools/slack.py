#!/usr/bin/env python3
"""
Slack notification wrapper. Posts to an incoming webhook.
Usage: python tools/slack.py "<message>"
If SLACK_WEBHOOK_URL is unset, appends to DAILY-SUMMARY.md fallback and exits 0.
"""
import json
import os
import sys
from datetime import datetime
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

if len(sys.argv) < 2 or not sys.argv[1].strip():
    print('Usage: python tools/slack.py "<message>"', file=sys.stderr)
    sys.exit(1)

msg = sys.argv[1]
webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
stamp = datetime.now().strftime("%Y-%m-%d %H:%M %Z")

if not webhook_url:
    fallback = Path(__file__).parent.parent / "DAILY-SUMMARY.md"
    with fallback.open("a") as f:
        f.write(f"\n---\n## {stamp} (fallback — Slack not configured)\n{msg}\n")
    print("[slack fallback] appended to DAILY-SUMMARY.md")
    print(msg)
    sys.exit(0)

r = requests.post(
    webhook_url,
    headers={"Content-Type": "application/json"},
    json={"text": msg},
    timeout=10,
)
r.raise_for_status()
print(f"[slack] message sent ({r.status_code})")
