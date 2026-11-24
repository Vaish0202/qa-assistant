"""List the Groq models your API key can use right now.

Usage:  python scripts/list_groq_models.py
Then put one of the printed ids in .env (GROQ_MODEL or JUDGE_MODEL).
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")
if not key:
    sys.exit("GROQ_API_KEY is not set in .env")

resp = requests.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {key}"},
    timeout=15,
)
if resp.status_code != 200:
    sys.exit(f"Groq returned {resp.status_code}: {resp.text[:300]}")

models = sorted(resp.json().get("data", []), key=lambda m: m["id"])
for m in models:
    if m.get("active", True):
        print(f"{m['id']:45s} owner={m.get('owned_by', '?'):12s} "
              f"context={m.get('context_window', '?')}")