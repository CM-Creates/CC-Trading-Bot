#!/usr/bin/env python3
"""
One-time Gmail OAuth2 setup. Run this once to authorize the bot to send email.
Requires credentials.json in the project root (downloaded from Google Cloud Console).

After running, token.json is saved locally and a base64 string is printed
for use in cloud routine environment variables (GMAIL_TOKEN_B64).
"""
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    import warnings
    warnings.filterwarnings("ignore")
except ImportError:
    print("ERROR: Run: pip3 install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.json"

if not CREDS_FILE.exists():
    print("ERROR: credentials.json not found in project root.")
    print()
    print("To get it:")
    print("  1. Go to https://console.cloud.google.com/")
    print("  2. Create a project (or select existing)")
    print("  3. APIs & Services → Enable APIs → search 'Gmail API' → Enable")
    print("  4. APIs & Services → Credentials → Create Credentials → OAuth client ID")
    print("  5. Application type: Desktop app → Create → Download JSON")
    print("  6. Rename the downloaded file to credentials.json")
    print("  7. Move it to:", ROOT)
    sys.exit(1)

print("Opening browser for Gmail authorization...")
print("Sign in with jamesonjeancharles2935@gmail.com and click Allow.")
print()

flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
creds = flow.run_local_server(port=0, open_browser=True)

TOKEN_FILE.write_text(creds.to_json())
print(f"✓ token.json saved to {TOKEN_FILE}")
print()

# Send a test email to confirm it works
try:
    import base64 as b64
    from email.mime.text import MIMEText

    service = build("gmail", "v1", credentials=creds)
    msg = MIMEText("Gmail OAuth2 is working. Your trading bot can now send email notifications.")
    msg["Subject"] = "Trading Bot — Gmail connected"
    msg["From"] = "jamesonjeancharles2935@gmail.com"
    msg["To"] = "jamesonjeancharles2935@gmail.com"
    raw = b64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print("✓ Test email sent to jamesonjeancharles2935@gmail.com")
except Exception as e:
    print(f"Warning: test email failed ({e})")

print()
print("=" * 60)
print("CLOUD ROUTINE SETUP (copy this for your routine env vars):")
print("=" * 60)
token_b64 = base64.b64encode(TOKEN_FILE.read_bytes()).decode()
print(f"GMAIL_TOKEN_B64={token_b64}")
print()
print("Add GMAIL_TOKEN_B64 as an environment variable in each")
print("cloud routine so notifications work in the cloud too.")
