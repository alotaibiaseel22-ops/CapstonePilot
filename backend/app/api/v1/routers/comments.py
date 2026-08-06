from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.comment import CommentCreate, CommentRead
from app.api.v1.deps import (
    Actor,
    get_comment_service,
    get_project_service,
    require_project_access,
)
from app.application.services.comment_service import (
    CommentNotFoundError,
    CommentService,
    EmptyCommentError,
    NotCommentAuthorError,
)
from app.application.services.project_service import ProjectService

router = APIRouter(tags=["comments"])


@router.post(
    "/projects/{project_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def post_comment(
    project_id: UUID,
    payload: CommentCreate,
    actor: Actor = Depends(require_project_access()),
    comment_service: CommentService = Depends(get_comment_service),
):
    try:
        comment = comment_service.post_comment(
            project_id,
            payload.body,
            author_id=actor.user.id if actor.kind == "user" else None,
            author_guest_id=actor.guest.id if actor.kind == "guest" else None,
        )
    except EmptyCommentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return CommentRead.model_validate(comment)


@router.get("/projects/{project_id}/comments", response_model=list[CommentRead])
def list_comments(
    project_id: UUID,
    _actor: Actor = Depends(require_project_access()),
    comment_service: CommentService = Depends(get_comment_service),
):
    return [CommentRead.model_validate(c) for c in comment_service.list_comments(project_id)]


@router.delete(
    "/projects/{project_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    project_id: UUID,
    comment_id: UUID,
    actor: Actor = Depends(require_project_access()),
    comment_service: CommentService = Depends(get_comment_service),
    project_service: ProjectService = Depends(get_project_service),
):
    try:
        project = project_service.get_project(project_id)
        comment_service.delete_comment(
            project_id,
            comment_id,
            requester_user_id=actor.user.id if actor.kind == "user" else None,
            requester_guest_id=actor.guest.id if actor.kind == "guest" else None,
            project_owner_id=project.owner_id,
        )
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotCommentAuthorError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
