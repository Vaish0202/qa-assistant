from typing import TypedDict, Optional

class AgentState(TypedDict):
    user_id: str
    testcase_logs: str
    testcase_description: str
    testcase_code: str
    classification: Optional[str]
    classification_confidence: Optional[float]
    analysis_type: Optional[str]
    framework: Optional[str]       
    test_type: Optional[str]        
    language: Optional[str]         
    jira_payload: Optional[dict]
    code_suggestions: Optional[list]
    channel_alert: Optional[str]
    final_output: Optional[dict]