#!/usr/bin/env python3
"""
Perplexity research wrapper. All market research goes through here.
Usage: python tools/perplexity.py "<query>"
Exits with code 3 if PERPLEXITY_API_KEY is unset — agent should fall back to WebSearch.
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

if len(sys.argv) < 2 or not sys.argv[1].strip():
    print('Usage: python tools/perplexity.py "<query>"', file=sys.stderr)
    sys.exit(1)

query = sys.argv[1]

API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
if not API_KEY:
    print("WARNING: PERPLEXITY_API_KEY not set. Fall back to WebSearch.", file=sys.stderr)
    sys.exit(3)

model = os.environ.get("PERPLEXITY_MODEL", "sonar")

payload = {
    "model": model,
    "messages": [
        {
            "role": "system",
            "content": "You are a precise financial research assistant. Cite every claim. Be concise.",
        },
        {"role": "user", "content": query},
    ],
}

r = requests.post(
    "https://api.perplexity.ai/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=30,
)
r.raise_for_status()
data = r.json()

# Print the assistant message text plus citations if present
content = data["choices"][0]["message"]["content"]
print(content)

citations = data.get("citations", [])
if citations:
    print("\nSources:")
    for i, url in enumerate(citations, 1):
        print(f"  [{i}] {url}")
