from database.models import Project, SessionLocal

def get_project_context(project_id: str) -> dict:
    """Fetch project details and build context string for agents"""
    if not project_id:
        return {"context_string": "", "project": None}

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"context_string": "", "project": None}

        tech = project.tech_stack or {}

        context_string = f"""
PROJECT CONTEXT:
- Project Name: {project.name}
- Description: {project.description}
- Frontend: {tech.get('frontend', 'Not specified')}
- Backend: {tech.get('backend', 'Not specified')}
- Database: {tech.get('database', 'Not specified')}
- Cloud: {tech.get('cloud', 'Not specified')}
- Test Framework: {project.test_framework}
- Language: {project.language}
- Jira Project: {project.jira_project_key}

Use this project context to give SPECIFIC suggestions
relevant to this exact tech stack.
"""
        return {
            "context_string": context_string,
            "project": {
                "id": project.id,
                "name": project.name,
                "tech_stack": tech,
                "test_framework": project.test_framework,
                "language": project.language,
                "jira_project_key": project.jira_project_key
            }
        }
    finally:
        db.close()