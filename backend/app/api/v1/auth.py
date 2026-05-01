from fastapi import APIRouter

from app.auth.security import create_token
from app.core.config import get_settings
from app.models.schemas import TokenRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def issue_demo_token(req: TokenRequest) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=create_token(req.user_id, req.role),
        expires_in_minutes=settings.jwt_expire_minutes,
    )
