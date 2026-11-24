"""Shows which Jira site/user the .env points to and whether project QA is visible."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()
url = (os.getenv("JIRA_URL") or "").rstrip("/")
key = os.getenv("JIRA_PROJECT_KEY", "QA")
auth = (os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
print("Site in .env:   ", url)

me = requests.get(f"{url}/rest/api/3/myself", auth=auth, timeout=15)
print("Logged in as:   ", me.json().get("emailAddress") if me.ok else f"FAILED {me.status_code}")

p = requests.get(f"{url}/rest/api/3/project/{key}", auth=auth, timeout=15)
if p.ok:
    print(f"Project {key}:     found ({p.json().get('name')})")
    print("Work types:     ", [t["name"] for t in p.json().get("issueTypes", [])])
else:
    print(f"Project {key}:     NOT visible ({p.status_code})")