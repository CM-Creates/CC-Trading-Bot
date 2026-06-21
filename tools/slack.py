#!/usr/bin/env python3
"""
Email notification wrapper (Gmail SMTP).
Usage: python tools/slack.py "<message>"
If GMAIL_APP_PASSWORD is unset, appends to DAILY-SUMMARY.md fallback and exits 0.
"""
import os
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

# Load .env if present
env_file = Path(__file__).parent.parent / ".env"
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
app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
email_from = os.environ.get("NOTIFY_EMAIL_FROM", "")
email_to = os.environ.get("NOTIFY_EMAIL_TO", "")
stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

if not app_password or not email_from or not email_to:
    fallback = Path(__file__).parent.parent / "DAILY-SUMMARY.md"
    with fallback.open("a") as f:
        f.write(f"\n---\n## {stamp} (fallback — email not configured)\n{msg_text}\n")
    print("[notify fallback] appended to DAILY-SUMMARY.md")
    print(msg_text)
    sys.exit(0)

# Build email
subject = f"Trading Bot — {stamp}"
msg = MIMEText(msg_text, "plain")
msg["Subject"] = subject
msg["From"] = email_from
msg["To"] = email_to

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(email_from, app_password)
    server.send_message(msg)

print(f"[notify] email sent to {email_to}")
