from fastapi import FastAPI
from app.api.routes.auth import router as auth_router

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