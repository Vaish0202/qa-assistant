import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "QA")

def get_auth():
    return (JIRA_EMAIL, JIRA_API_TOKEN)

def get_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def create_jira_ticket(payload: dict) -> dict:
    url = f"{JIRA_URL}/rest/api/3/issue"

    description_text = f"""Bug detected by QA Assistant

Summary: {payload.get('summary', '')}

Steps to reproduce:
{chr(10).join([f"- {s}" for s in payload.get('steps_to_reproduce', [])])}

Expected: {payload.get('expected_result', '')}
Actual: {payload.get('actual_result', '')}

Suggested fix: {payload.get('suggested_fix', '')}"""

    body = {
        "fields": {
            "project": {"key": payload.get('project_key', JIRA_PROJECT_KEY)},
            "summary": payload.get('summary', 'Bug detected by QA Assistant'),
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description_text}]
                    }
                ]
            },
            "issuetype": {"name": "Bug"},
            "priority": {"name": severity_to_priority(payload.get('severity', 'medium'))}
        }
    }

    response = requests.post(
        url,
        data=json.dumps(body),
        auth=get_auth(),
        headers=get_headers()
    )

    if response.status_code == 201:
        data = response.json()
        ticket_key = data['key']
        ticket_url = f"{JIRA_URL}/browse/{ticket_key}"
        print(f"✓ Jira ticket created: {ticket_key}")
        return {"success": True, "ticket_key": ticket_key, "ticket_url": ticket_url}
    else:
        print(f"✗ Ticket creation failed: {response.status_code} - {response.text}")
        return {"success": False, "error": response.text, "status_code": response.status_code}

def severity_to_priority(severity: str) -> str:
    mapping = {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium",
        "low": "Low"
    }
    return mapping.get(severity.lower(), "Medium")