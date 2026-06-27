from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from backend.database import get_db
from backend.models.user import User
from backend.models.study_plan import StudyPlan
from backend.auth import get_current_user
from backend.services.ai_service import generate_study_plan

router = APIRouter(prefix="/study-plan", tags=["study-plan"])


@router.post("/generate")
async def generate_plan(
    days: int = Query(7, ge=3, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new study plan for N days using Grok."""
    result = await generate_study_plan(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        days=days
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/latest")
async def get_latest_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the most recently generated study plan."""
    result = await db.execute(
        select(StudyPlan)
        .where(StudyPlan.user_id == current_user.id)
        .order_by(StudyPlan.generated_at.desc())
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        return None

    try:
        parsed_plan = json.loads(plan.plan_data)
    except:
        parsed_plan = {}

    return {
        "generatedAt": plan.generated_at.isoformat() if plan.generated_at else None,
        "durationDays": plan.duration_days,
        "plan": parsed_plan.get("plan", [])
    }
