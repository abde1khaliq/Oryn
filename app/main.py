from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.api.routes.tenant import router as tenant_router
from app.api.routes.invitation import router as invitation_router
from app.api.routes.profile import router as profile_router
from app.api.routes.teams import router as team_router
from app.api.routes.projects import router as project_router
from app.api.routes.tasks import router as task_router
from app.api.routes.comments import router as comment_router
from app.api.routes.billing import router as billing_router

app = FastAPI(title='Oryn', description="""
A backend API where companies sign up, get their own private workspace, 
and inside it they manage their teams, projects, and tasks — think a simplified Jira or Asana.
""")

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": "Oryn"
    }

app.include_router(auth_router, prefix='/auth', tags=['Authentication Layer'])
app.include_router(profile_router, tags=["Profile"])
app.include_router(tenant_router, prefix='/workspace', tags=['Workspace Endpoints'])
app.include_router(invitation_router, prefix='/workspace', tags=['Workspace Invitation Endpoints'])
app.include_router(team_router, prefix='/workspace', tags=['Workspace Teams Endpoints'])
app.include_router(project_router, prefix='/workspace', tags=["Team Projects"])
app.include_router(task_router, prefix='/workspace', tags=['Tasks'])
app.include_router(comment_router, prefix='/workspace', tags=['Comments'])
app.include_router(billing_router, prefix="/billing", tags=["Billing"])