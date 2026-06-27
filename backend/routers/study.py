"""
Study session & heartbeat router.
Tracks active study time via a heartbeat-based approach:
  1. Client starts a session (POST /study/start)
  2. Client pings heartbeats every 30s (POST /study/heartbeat)
  3. Client ends the session (POST /study/end)
  4. Duration is computed from first heartbeat to last.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta

from backend.database import get_db
from backend.models.user import User
from backend.models.study import StudySession, Heartbeat
from backend.auth import get_current_user

router = APIRouter(prefix="/study", tags=["study"])


# --- Schemas -----------------------------------------------------------------

class StartSessionRequest(BaseModel):
    problem_id: int | None = None


class StartSessionResponse(BaseModel):
    session_id: int
    started_at: str


class HeartbeatResponse(BaseModel):
    session_id: int
    heartbeat_count: int
    elapsed_seconds: int


class EndSessionResponse(BaseModel):
    session_id: int
    duration_seconds: int
    started_at: str
    ended_at: str


class StudyStatsResponse(BaseModel):
    today_minutes: int
    week_minutes: int
    total_minutes: int
    total_sessions: int


# --- Endpoints ---------------------------------------------------------------

@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    payload: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new study session. Ends any active session first."""
    # Auto-end any existing active session
    result = await db.execute(
        select(StudySession).where(
            StudySession.user_id == current_user.id,
            StudySession.ended_at.is_(None),
        )
    )
    active = result.scalar_one_or_none()
    if active:
        active.ended_at = datetime.now(timezone.utc)
        active.duration_seconds = int(
            (active.ended_at - active.started_at).total_seconds()
        )

    session = StudySession(
        user_id=current_user.id,
        problem_id=payload.problem_id,
    )
    db.add(session)
    await db.flush()

    # First heartbeat
    hb = Heartbeat(session_id=session.id)
    db.add(hb)
    await db.commit()

    return StartSessionResponse(
        session_id=session.id,
        started_at=session.started_at.isoformat(),
    )


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ping heartbeat for the current active session."""
    result = await db.execute(
        select(StudySession).where(
            StudySession.user_id == current_user.id,
            StudySession.ended_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active study session")

    hb = Heartbeat(session_id=session.id)
    db.add(hb)
    await db.flush()

    # Count heartbeats
    count_result = await db.execute(
        select(func.count(Heartbeat.id)).where(Heartbeat.session_id == session.id)
    )
    count = count_result.scalar() or 0

    elapsed = int((datetime.now(timezone.utc) - session.started_at.replace(tzinfo=timezone.utc)).total_seconds())
    await db.commit()

    return HeartbeatResponse(
        session_id=session.id,
        heartbeat_count=count,
        elapsed_seconds=elapsed,
    )


@router.post("/end", response_model=EndSessionResponse)
async def end_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """End the current active study session."""
    result = await db.execute(
        select(StudySession).where(
            StudySession.user_id == current_user.id,
            StudySession.ended_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active study session")

    now = datetime.now(timezone.utc)
    started = session.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)

    session.ended_at = now
    session.duration_seconds = int((now - started).total_seconds())
    await db.commit()

    return EndSessionResponse(
        session_id=session.id,
        duration_seconds=session.duration_seconds,
        started_at=started.isoformat(),
        ended_at=now.isoformat(),
    )


@router.get("/stats", response_model=StudyStatsResponse)
async def study_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get study time statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    # Today
    today_result = await db.execute(
        select(func.coalesce(func.sum(StudySession.duration_seconds), 0)).where(
            StudySession.user_id == current_user.id,
            StudySession.duration_seconds.is_not(None),
            StudySession.started_at >= today_start,
        )
    )
    today_secs = today_result.scalar() or 0

    # This week
    week_result = await db.execute(
        select(func.coalesce(func.sum(StudySession.duration_seconds), 0)).where(
            StudySession.user_id == current_user.id,
            StudySession.duration_seconds.is_not(None),
            StudySession.started_at >= week_start,
        )
    )
    week_secs = week_result.scalar() or 0

    # All time
    total_result = await db.execute(
        select(func.coalesce(func.sum(StudySession.duration_seconds), 0)).where(
            StudySession.user_id == current_user.id,
            StudySession.duration_seconds.is_not(None),
        )
    )
    total_secs = total_result.scalar() or 0

    # Session count
    count_result = await db.execute(
        select(func.count(StudySession.id)).where(
            StudySession.user_id == current_user.id,
            StudySession.duration_seconds.is_not(None),
        )
    )
    total_sessions = count_result.scalar() or 0

    return StudyStatsResponse(
        today_minutes=today_secs // 60,
        week_minutes=week_secs // 60,
        total_minutes=total_secs // 60,
        total_sessions=total_sessions,
    )
