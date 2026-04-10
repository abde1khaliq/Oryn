from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.session import get_db
from app.schemas.task import TaskCreationForm, TaskUpdateForm, TaskStatusUpdateForm, TaskView
from app.services.task_service import (
    verify_project_chain, create_task, get_tasks, get_task,
    update_task, update_task_status, delete_task
)

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/tasks",
    tags=["Tasks"]
)

@router.post("", summary="Create a task", description="Creates a new task inside a project. All workspace members can create tasks. The assignee must be a member of the same workspace.")
async def create_task_route(form: TaskCreationForm, team_id: UUID, project_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await verify_project_chain(db, current_user.tenant_id, team_id, project_id)
    task = await create_task(db, current_user.tenant_id, current_user.id, project, form)
    return {"message": "Task created successfully.", "task": {"id": task.id, "title": task.title, "status": task.status}}

@router.get("", summary="Get all tasks in a project", description="Returns all tasks belonging to a specific project.")
async def get_project_tasks_route(team_id: UUID, project_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await verify_project_chain(db, current_user.tenant_id, team_id, project_id)
    tasks = await get_tasks(db, current_user.tenant_id, project)
    return {"project": project.name, "tasks": [{"id": t.id, "title": t.title, "description": t.description, "status": t.status, "assigned_to": t.assigned_to, "created_at": t.created_at} for t in tasks]}

@router.get("/{task_id}", response_model=TaskView, summary="Get a task", description="Returns details of a specific task inside a project.")
async def get_task_route(team_id: UUID, project_id: UUID, task_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await verify_project_chain(db, current_user.tenant_id, team_id, project_id)
    return await get_task(db, current_user.tenant_id, project_id, task_id)

@router.patch("/{task_id}", summary="Update a task", description="Updates a task's title, description, or assignee.")
async def update_task_route(form: TaskUpdateForm, team_id: UUID, project_id: UUID, task_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await verify_project_chain(db, current_user.tenant_id, team_id, project_id)
    task = await update_task(db, current_user.tenant_id, project_id, task_id, form, current_user)
    return {"message": "Task updated successfully.", "task": {"id": task.id, "title": task.title, "status": task.status}}

@router.patch("/{task_id}/status", summary="Update task status", description="Updates the status of a task. Valid statuses are: todo, in_progress, in_review, done.")
async def update_task_status_route(form: TaskStatusUpdateForm, team_id: UUID, project_id: UUID, task_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await verify_project_chain(db, current_user.tenant_id, team_id, project_id)
    task = await update_task_status(db, current_user.tenant_id, project_id, task_id, form.status)
    return {"message": f"Task status updated to '{form.status}'."}

@router.delete("/{task_id}", summary="Delete a task", description="Permanently deletes a task. Only owners and admins can delete tasks.")
async def delete_task_route(team_id: UUID, project_id: UUID, task_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await verify_project_chain(db, current_user.tenant_id, team_id, project_id)
    task = await delete_task(db, current_user.tenant_id, project_id, task_id, current_user)
    return {"message": f"Task '{task.title}' has been deleted."}
