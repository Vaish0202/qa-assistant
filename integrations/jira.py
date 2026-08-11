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

def validate_jira_config() -> bool:
    """Check if Jira is properly configured"""
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        print("✗ Jira not configured — missing env variables")
        return False
    return True

def truncate_summary(summary: str, max_length: int = 200) -> str:
    """Jira summary has max length limit"""
    if not summary:
        return "Bug detected by QA Assistant"
    return summary[:max_length] if len(summary) > max_length else summary

def build_jira_description(payload: dict) -> dict:
    """Build Atlassian Document Format description"""
    parts = []

    if payload.get('description'):
        parts.append(payload['description'])

    if payload.get('steps_to_reproduce'):
        steps = '\n'.join([f"  {i+1}. {s}"
                          for i, s in enumerate(payload['steps_to_reproduce'])])
        parts.append(f"\nSteps to reproduce:\n{steps}")

    if payload.get('expected_result'):
        parts.append(f"\nExpected: {payload['expected_result']}")

    if payload.get('actual_result'):
        parts.append(f"\nActual: {payload['actual_result']}")

    if payload.get('suggested_fix'):
        parts.append(f"\nSuggested fix: {payload['suggested_fix']}")

    if payload.get('framework'):
        parts.append(f"\nFramework: {payload['framework']}")

    description_text = '\n'.join(parts) or "Bug detected by QA Assistant"

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": description_text}
                ]
            }
        ]
    }

def create_jira_ticket(payload: dict) -> dict:
    """Create a real Jira ticket with retry logic"""
    if not validate_jira_config():
        return {
            "success": False,
            "error": "Jira not configured",
            "ticket_key": None
        }

    url = f"{JIRA_URL}/rest/api/3/issue"
    summary = truncate_summary(payload.get('summary', 'Bug detected by QA Assistant'))
    description = build_jira_description(payload)
    priority = severity_to_priority(payload.get('severity', 'medium'))
    project_key = payload.get('project_key', JIRA_PROJECT_KEY) or JIRA_PROJECT_KEY

    body = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Bug"},
            "priority": {"name": priority}
        }
    }

    # Try with priority first
    for attempt in range(2):
        try:
            if attempt == 1:
                # Second attempt without priority (some Jira configs don't allow it)
                body["fields"].pop("priority", None)
                print("Retrying without priority field...")

            response = requests.post(
                url,
                data=json.dumps(body),
                auth=get_auth(),
                headers=get_headers(),
                timeout=30
            )

            if response.status_code == 201:
                data = response.json()
                ticket_key = data['key']
                ticket_url = f"{JIRA_URL}/browse/{ticket_key}"
                print(f"✓ Jira ticket created: {ticket_key}")
                return {
                    "success": True,
                    "ticket_key": ticket_key,
                    "ticket_url": ticket_url
                }
            else:
                error_text = response.text
                print(f"✗ Attempt {attempt+1} failed: {response.status_code} - {error_text[:200]}")
                if attempt == 1:
                    return {
                        "success": False,
                        "error": error_text,
                        "status_code": response.status_code
                    }

        except requests.exceptions.Timeout:
            print("✗ Jira request timed out")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"✗ Jira error: {str(e)}")
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "All attempts failed"}

def severity_to_priority(severity: str) -> str:
    mapping = {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium",
        "low": "Low"
    }
    return mapping.get(severity.lower() if severity else 'medium', "Medium")