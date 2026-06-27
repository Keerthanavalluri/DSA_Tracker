from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from backend.database import get_db
from backend.models.user import User
from backend.models.submission import Submission, VerdictEnum
from backend.models.problem import Problem
from backend.models.topic_matrix import TopicMatrix
from backend.models.study import Streak
from backend.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/heatmap")
async def submission_heatmap(
    days: int = Query(default=365, ge=30, le=730),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns {date: count} for the last N days.
    Used to render the contribution heatmap calendar.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Submission.submitted_at)
        .where(
            Submission.user_id == current_user.id,
            Submission.submitted_at >= since,
        )
    )
    rows = result.fetchall()

    heatmap: dict[str, int] = defaultdict(int)
    for (submitted_at,) in rows:
        day = submitted_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
        heatmap[day] += 1

    return {"heatmap": dict(heatmap)}


@router.get("/topic-matrix")
async def topic_matrix(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Full topic matrix for the user.
    Returns list of {topic, solved, failed, avgDifficulty, lastPracticed}.
    Sorted by weakness score (high fail rate first).
    """
    result = await db.execute(
        select(TopicMatrix)
        .where(TopicMatrix.user_id == current_user.id)
        .order_by(TopicMatrix.solved_count.asc())
    )
    rows = result.scalars().all()

    data = []
    for tm in rows:
        total = tm.solved_count + tm.failed_count
        fail_rate = tm.failed_count / total if total > 0 else 0
        data.append({
            "topic": tm.topic,
            "solved": tm.solved_count,
            "failed": tm.failed_count,
            "total": total,
            "failRate": round(fail_rate, 3),
            "avgDifficulty": tm.avg_difficulty,
            "lastPracticed": tm.last_practiced_at.isoformat() if tm.last_practiced_at else None,
            "weaknessScore": round(fail_rate * tm.avg_difficulty, 3),
        })

    # Sort by weakness score descending
    data.sort(key=lambda x: x["weaknessScore"], reverse=True)
    return {"topics": data}


@router.get("/stats")
async def overall_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Summary stats: total solved, by difficulty, by platform, streak.
    """
    # Total AC submissions (unique problems)
    total_result = await db.execute(
        select(func.count(func.distinct(Submission.problem_id)))
        .where(
            Submission.user_id == current_user.id,
            Submission.status == VerdictEnum.AC,
        )
    )
    total_solved = total_result.scalar() or 0

    # By difficulty
    diff_result = await db.execute(
        select(Problem.difficulty, func.count(func.distinct(Submission.problem_id)))
        .join(Problem, Submission.problem_id == Problem.id)
        .where(
            Submission.user_id == current_user.id,
            Submission.status == VerdictEnum.AC,
        )
        .group_by(Problem.difficulty)
    )
    by_difficulty = {"easy": 0, "medium": 0, "hard": 0}
    diff_map = {1: "easy", 2: "medium", 3: "hard"}
    for diff, count in diff_result.fetchall():
        if diff in diff_map:
            by_difficulty[diff_map[diff]] = count

    # By platform
    plat_result = await db.execute(
        select(Problem.platform, func.count(func.distinct(Submission.problem_id)))
        .join(Problem, Submission.problem_id == Problem.id)
        .where(
            Submission.user_id == current_user.id,
            Submission.status == VerdictEnum.AC,
        )
        .group_by(Problem.platform)
    )
    by_platform = {}
    for platform, count in plat_result.fetchall():
        by_platform[platform] = count

    # Streak
    streak_result = await db.execute(
        select(Streak).where(Streak.user_id == current_user.id)
    )
    streak = streak_result.scalar_one_or_none()

    # Total submissions
    total_subs_result = await db.execute(
        select(func.count(Submission.id)).where(Submission.user_id == current_user.id)
    )
    total_submissions = total_subs_result.scalar() or 0

    return {
        "totalSolved": total_solved,
        "totalSubmissions": total_submissions,
        "acceptanceRate": round(total_solved / total_submissions * 100, 1) if total_submissions > 0 else 0,
        "byDifficulty": by_difficulty,
        "byPlatform": by_platform,
        "currentStreak": streak.current_streak if streak else 0,
        "longestStreak": streak.longest_streak if streak else 0,
        "lastActiveDate": streak.last_active_date if streak else None,
    }


@router.get("/submissions")
async def recent_submissions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None),
    verdict: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated submission history with problem details."""
    query = (
        select(Submission, Problem)
        .join(Problem, Submission.problem_id == Problem.id)
        .where(Submission.user_id == current_user.id)
    )

    if platform:
        query = query.where(Problem.platform == platform)
    if verdict:
        query = query.where(Submission.status == verdict)

    query = query.order_by(Submission.submitted_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)

    return {
        "submissions": [
            {
                "id": sub.id,
                "problem": {
                    "id": prob.id,
                    "title": prob.title,
                    "slug": prob.slug,
                    "platform": prob.platform,
                    "difficulty": prob.difficulty,
                    "tags": prob.tags,
                    "url": prob.url,
                },
                "status": sub.status,
                "language": sub.language,
                "timeMs": sub.time_ms,
                "memoryKb": sub.memory_kb,
                "submittedAt": sub.submitted_at.isoformat(),
            }
            for sub, prob in result.fetchall()
        ]
    }
