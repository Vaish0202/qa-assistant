from integrations.jira import create_jira_ticket
from dotenv import load_dotenv
load_dotenv()

result = create_jira_ticket({
    "project_key": "QA",
    "summary": "Test ticket from QA Assistant",
    "description": "Test bug ticket created by AI",
    "severity": "medium",
    "bug_type": "backend",
    "steps_to_reproduce": ["Run test", "See failure"],
    "expected_result": "Test should pass",
    "actual_result": "Test failed with error",
    "suggested_fix": "Check backend logs"
})
print(result)