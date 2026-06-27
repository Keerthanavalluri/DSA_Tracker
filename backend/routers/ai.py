from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.auth import get_current_user
from backend.services.ai_service import get_or_generate_recommendation

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze")
async def analyze(
    force_refresh: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger AI weakness analysis using Grok.
    Cached for 24h unless force_refresh=true.
    """
    result = await get_or_generate_recommendation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        force_refresh=force_refresh,
    )
    return result


@router.get("/recommendations")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest cached AI recommendation."""
    result = await get_or_generate_recommendation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        force_refresh=False,
    )
    return result
