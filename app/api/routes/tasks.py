# app/api/routes/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.task import TaskCreationForm, TaskUpdateForm, TaskStatusUpdateForm, TaskView
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.task import Task
from app.models.project import Project
from app.models.team import Team
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/tasks",
    tags=["Tasks"]
)

VALID_STATUSES = ["todo", "in_progress", "in_review", "done"]


async def verify_project(team_id: UUID, project_id: UUID, current_user: User, db: AsyncSession) -> Project:
    """Verifies the team and project exist and belong to the current user's workspace."""
    team_result = await db.execute(
        select(Team).where(
            Team.id == team_id,
            Team.tenant_id == current_user.tenant_id
        )
    )
    if not team_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found.")

    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.team_id == team_id,
            Project.tenant_id == current_user.tenant_id
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    return project


@router.post(
    "",
    summary="Create a task",
    description="Creates a new task inside a project. All workspace members can create tasks. The assignee must be a member of the same workspace."
)
async def create_task_route(
    form: TaskCreationForm,
    team_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project = await verify_project(team_id, project_id, current_user, db)

    # verify assignee exists in this workspace if provided
    if form.assigned_to:
        assignee_result = await db.execute(
            select(User).where(
                User.id == form.assigned_to,
                User.tenant_id == current_user.tenant_id
            )
        )
        if not assignee_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Assigned user not found in this workspace.")

    new_task = Task(
        title=form.title,
        description=form.description,
        assigned_to=form.assigned_to,
        project_id=project.id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        status="todo"
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return {
        "message": "Task created successfully.",
        "task": {"id": new_task.id, "title": new_task.title, "status": new_task.status}
    }


@router.get(
    "",
    summary="Get all tasks in a project",
    description="Returns all tasks belonging to a specific project."
)
async def get_project_tasks_route(
    team_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project = await verify_project(team_id, project_id, current_user, db)

    query_result = await db.execute(
        select(Task).where(
            Task.project_id == project.id,
            Task.tenant_id == current_user.tenant_id
        )
    )
    tasks = query_result.scalars().all()

    return {
        "project": project.name,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at
            }
            for task in tasks
        ]
    }


@router.get(
    "/{task_id}",
    response_model=TaskView,
    summary="Get a task",
    description="Returns details of a specific task inside a project."
)
async def get_task_route(
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_project(team_id, project_id, current_user, db)

    task_result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.tenant_id == current_user.tenant_id
        )
    )
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task


@router.patch(
    "/{task_id}",
    summary="Update a task",
    description="Updates a task's title, description, or assignee."
)
async def update_task_route(
    form: TaskUpdateForm,
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_project(team_id, project_id, current_user, db)

    task_result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.tenant_id == current_user.tenant_id
        )
    )
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    # verify new assignee exists in workspace if provided
    if form.assigned_to:
        assignee_result = await db.execute(
            select(User).where(
                User.id == form.assigned_to,
                User.tenant_id == current_user.tenant_id
            )
        )
        if not assignee_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Assigned user not found in this workspace.")

    if form.title:
        task.title = form.title
    if form.description:
        task.description = form.description
    if form.assigned_to:
        task.assigned_to = form.assigned_to

    await db.commit()
    await db.refresh(task)

    return {
        "message": "Task updated successfully.",
        "task": {"id": task.id, "title": task.title, "status": task.status}
    }


@router.patch(
    "/{task_id}/status",
    summary="Update task status",
    description="Updates the status of a task. Valid statuses are: todo, in_progress, in_review, done."
)
async def update_task_status_route(
    form: TaskStatusUpdateForm,
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if form.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid options are: {', '.join(VALID_STATUSES)}"
        )

    await verify_project(team_id, project_id, current_user, db)

    task_result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.tenant_id == current_user.tenant_id
        )
    )
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    task.status = form.status
    await db.commit()

    return {"message": f"Task status updated to '{form.status}'."}


@router.delete(
    "/{task_id}",
    summary="Delete a task",
    description="Permanently deletes a task. Only owners and admins can delete tasks."
)
async def delete_task_route(
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can delete tasks.")

    await verify_project(team_id, project_id, current_user, db)

    task_result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.tenant_id == current_user.tenant_id
        )
    )
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    await db.delete(task)
    await db.commit()

    return {"message": f"Task '{task.title}' has been deleted."}