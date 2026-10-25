from fastapi import APIRouter, Depends

from ...core.auth import get_current_user
from ...models.user import User
from ...schemas import ActionDraftRequest, ActionDraftResponse
from ...services.actions import draft_action

router = APIRouter()


@router.post(
    "/v1/actions/draft",
    response_model=ActionDraftResponse,
    tags=["Recovery"],
)
async def create_action_draft(
    payload: ActionDraftRequest,
    user: User = Depends(get_current_user),
):
    return draft_action(payload)
