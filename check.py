import os
from dotenv import load_dotenv
load_dotenv(override=True)

for k in ["LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT",
          "LANGSMITH_PROJECT", "LANGSMITH_WORKSPACE_ID",
          "LANGCHAIN_API_KEY", "LANGCHAIN_ENDPOINT"]:
    v = os.getenv(k)
    print(f"{k:24s}", (v[:10] + "..." + f" (len {len(v)})") if v and "KEY" in k else v)

from langsmith import Client
print(Client().list_projects(limit=3) and [p.name for p in Client().list_projects(limit=3)])