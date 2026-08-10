import requests, os, json
from dotenv import load_dotenv
load_dotenv()

r = requests.get(
    os.getenv('JIRA_URL') + '/rest/api/3/search/jql?jql=project=10033&maxResults=20&fields=summary,status,priority',
    auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN')),
    headers={"Accept": "application/json"}
)
data = r.json()
print(f"Total tickets found: {len(data.get('issues', []))}")
for issue in data.get('issues', []):
    fields = issue.get('fields', {})
    summary = fields.get('summary', 'No summary') if fields else 'No fields'
    print(f"  ID: {issue['id']} | {summary}")