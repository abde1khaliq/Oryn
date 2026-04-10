# app/api/routes/comments.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.comment import CommentCreationForm, CommentUpdateForm, CommentView
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.comment import Comment
from app.models.task import Task
from app.models.project import Project
from app.models.team import Team
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/tasks/{task_id}/comments",
    tags=["Comments"]
)


async def verify_task(
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    current_user: User,
    db: AsyncSession
) -> Task:
    """Verifies the full chain — team → project → task — all belong to the current workspace."""
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
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found.")

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


@router.post(
    "",
    summary="Add a comment to a task",
    description="Adds a comment to a specific task. Any workspace member can comment."
)
async def create_comment_route(
    form: CommentCreationForm,
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = await verify_task(team_id, project_id, task_id, current_user, db)

    new_comment = Comment(
        body=form.body,
        task_id=task.id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return {
        "message": "Comment added successfully.",
        "comment": {"id": new_comment.id, "body": new_comment.body, "created_at": new_comment.created_at}
    }


@router.get(
    "",
    summary="Get all comments on a task",
    description="Returns all comments on a specific task ordered by creation date."
)
async def get_task_comments_route(
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = await verify_task(team_id, project_id, task_id, current_user, db)

    query_result = await db.execute(
        select(Comment).where(
            Comment.task_id == task.id,
            Comment.tenant_id == current_user.tenant_id
        ).order_by(Comment.created_at.asc())
    )
    comments = query_result.scalars().all()

    return {
        "task": task.title,
        "comments": [
            {
                "id": comment.id,
                "body": comment.body,
                "created_by": comment.created_by,
                "created_at": comment.created_at
            }
            for comment in comments
        ]
    }


@router.patch(
    "/{comment_id}",
    summary="Edit a comment",
    description="Updates the body of a comment. Only the author of the comment can edit it."
)
async def update_comment_route(
    form: CommentUpdateForm,
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_task(team_id, project_id, task_id, current_user, db)

    comment_result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.task_id == task_id,
            Comment.tenant_id == current_user.tenant_id
        )
    )
    comment = comment_result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    if comment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments.")

    comment.body = form.body
    await db.commit()
    await db.refresh(comment)

    return {
        "message": "Comment updated successfully.",
        "comment": {"id": comment.id, "body": comment.body}
    }


@router.delete(
    "/{comment_id}",
    summary="Delete a comment",
    description="Deletes a comment. Authors can delete their own comments. Owners and admins can delete any comment."
)
async def delete_comment_route(
    team_id: UUID,
    project_id: UUID,
    task_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_task(team_id, project_id, task_id, current_user, db)

    comment_result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.task_id == task_id,
            Comment.tenant_id == current_user.tenant_id
        )
    )
    comment = comment_result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    # authors can delete their own, owners and admins can delete any
    if comment.created_by != current_user.id and current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this comment.")

    await db.delete(comment)
    await db.commit()

    return {"message": "Comment deleted successfully."}