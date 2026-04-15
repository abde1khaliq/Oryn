from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.session import get_db
from app.schemas.comment import CommentCreationForm, CommentUpdateForm, CommentView
from app.api.dependencies import require_feature
from app.core.limiter import limiter
from app.services.comment_service import (
    verify_task_chain, create_comment, get_comments,
    update_comment, delete_comment
)


router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/tasks/{task_id}/comments",
    tags=["Comments"]
)

@router.post(
    "", 
    summary="Add a comment to a task", 
    description="Adds a comment to a specific task. Any workspace member can comment."
)
@limiter.limit("5/minute")
async def create_comment_route(
    request: Request,
    form: CommentCreationForm, 
    team_id: UUID, 
    project_id: UUID, 
    task_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_feature("task_comments")),
):
    task = await verify_task_chain(db, current_user.tenant_id, team_id, project_id, task_id)
    comment = await create_comment(db, current_user.tenant_id, current_user.id, task, form.body)
    return {"message": "Comment added successfully.", "comment": {"id": comment.id, "body": comment.body, "created_at": comment.created_at}}

@router.get(
    "", 
    summary="Get all comments on a task", 
    description="Returns all comments on a specific task ordered by creation date."
)
@limiter.limit("5/minute")
async def get_task_comments_route(
    request: Request,
    team_id: UUID, 
    project_id: UUID, 
    task_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    task = await verify_task_chain(db, current_user.tenant_id, team_id, project_id, task_id)
    comments = await get_comments(db, current_user.tenant_id, task)
    return {
        "task": task.title, 
        "comments": [
            {
                "id": c.id, 
                "body": c.body, 
                "created_by": c.created_by, 
                "created_at": c.created_at
            } for c in comments
        ]
    }

@router.patch(
    "/{comment_id}", 
    summary="Edit a comment", 
    description="Updates the body of a comment. Only the author of the comment can edit it."
)
@limiter.limit("5/minute")
async def update_comment_route(
    request: Request,
    form: CommentUpdateForm, 
    team_id: UUID, 
    project_id: UUID, 
    task_id: UUID, 
    comment_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    await verify_task_chain(db, current_user.tenant_id, team_id, project_id, task_id)
    comment = await update_comment(db, current_user.tenant_id, task_id, comment_id, current_user.id, form.body)
    return {"message": "Comment updated successfully.", "comment": {"id": comment.id, "body": comment.body}}

@router.delete(
    "/{comment_id}", 
    summary="Delete a comment", 
    description="Deletes a comment. Authors can delete their own comments. Owners and admins can delete any comment."
)
@limiter.limit("5/minute")
async def delete_comment_route(
    request: Request,
    team_id: UUID, 
    project_id: UUID, 
    task_id: UUID, 
    comment_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    await verify_task_chain(db, current_user.tenant_id, team_id, project_id, task_id)
    await delete_comment(db, current_user.tenant_id, task_id, comment_id, current_user)
    return {"message": "Comment deleted successfully."}
