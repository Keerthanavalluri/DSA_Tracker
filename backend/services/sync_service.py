"""
Sync service — ingests submissions from platforms into the database.
Handles deduplication, problem upserts, topic matrix recomputation.
"""

import json
from datetime import datetime, timezone, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.models.problem import Problem
from backend.models.submission import Submission, VerdictEnum
from backend.models.platform import PlatformAccount
from backend.models.topic_matrix import TopicMatrix
from backend.models.study import Streak


async def upsert_problem(db: AsyncSession, data: dict) -> Problem:
    """Get or create a Problem row. Returns the Problem ORM object."""
    result = await db.execute(
        select(Problem).where(
            Problem.platform == data["platform"],
            Problem.platform_problem_id == data["platform_problem_id"],
        )
    )
    problem = result.scalar_one_or_none()

    if problem is None:
        problem = Problem(
            platform=data["platform"],
            platform_problem_id=data["platform_problem_id"],
            slug=data["slug"],
            title=data["title"],
            difficulty=data["difficulty"],
            tags=data["tags"],
            url=data.get("url"),
            cf_rating=data.get("cf_rating"),
        )
        db.add(problem)
        await db.flush()
    else:
        # Update tags/difficulty/rating if we have better info
        if data.get("cf_rating") and not problem.cf_rating:
            problem.cf_rating = data["cf_rating"]
        if data.get("tags") and not problem.tags:
            problem.tags = data["tags"]
        if data.get("difficulty") and not problem.difficulty:
            problem.difficulty = data["difficulty"]

    return problem


async def sync_submissions(
    db: AsyncSession,
    user_id: int,
    raw_submissions: list[dict],
) -> dict:
    """
    Optimized sync of raw submissions. Batch queries problems and processes in memory.
    Returns summary: {new_problems, new_submissions, skipped}
    """
    if not raw_submissions:
        return {"new_problems": 0, "new_submissions": 0, "skipped": 0}

    # Fetch existing platform_submission_ids to avoid duplicates
    existing_result = await db.execute(
        select(Submission.platform_submission_id).where(
            Submission.user_id == user_id,
            Submission.platform_submission_id.is_not(None)
        )
    )
    existing_ids = {row[0] for row in existing_result.fetchall()}

    # Filter out already synced submissions
    pending_submissions = []
    skipped = 0
    for sub in raw_submissions:
        pid = sub.get("platform_submission_id", "")
        if pid and pid in existing_ids:
            skipped += 1
        else:
            pending_submissions.append(sub)

    if not pending_submissions:
        return {"new_problems": 0, "new_submissions": 0, "skipped": skipped}

    # Get all unique problems in pending
    platform = pending_submissions[0]["platform"]
    unique_problem_ids = list({sub["platform_problem_id"] for sub in pending_submissions})

    # Fetch existing problems from database in chunks of 500 to avoid parameters limit
    existing_problems = {}
    chunk_size = 500
    for i in range(0, len(unique_problem_ids), chunk_size):
        chunk = unique_problem_ids[i:i+chunk_size]
        q = select(Problem).where(
            Problem.platform == platform,
            Problem.platform_problem_id.in_(chunk)
        )
        res = await db.execute(q)
        for p in res.scalars().all():
            existing_problems[p.platform_problem_id] = p

    # Create missing problems
    new_problems_count = 0
    problem_map = {**existing_problems}
    
    missing_data_map = {}
    for sub in pending_submissions:
        ppid = sub["platform_problem_id"]
        if ppid not in problem_map and ppid not in missing_data_map:
            missing_data_map[ppid] = sub

    for ppid, sub in missing_data_map.items():
        problem = Problem(
            platform=sub["platform"],
            platform_problem_id=ppid,
            slug=sub["slug"],
            title=sub["title"],
            difficulty=sub["difficulty"],
            tags=sub["tags"],
            url=sub.get("url"),
            cf_rating=sub.get("cf_rating"),
        )
        db.add(problem)
        problem_map[ppid] = problem
        new_problems_count += 1

    if new_problems_count > 0:
        await db.flush()  # Populate IDs for new problems

    # Create submissions
    new_submissions_count = 0
    for sub in pending_submissions:
        ppid = sub["platform_problem_id"]
        problem = problem_map.get(ppid)
        if not problem:
            continue
        
        # Update existing problem fields if they are missing
        if sub.get("cf_rating") and not problem.cf_rating:
            problem.cf_rating = sub["cf_rating"]
        if sub.get("tags") and not problem.tags:
            problem.tags = sub["tags"]
        if sub.get("difficulty") and not problem.difficulty:
            problem.difficulty = sub["difficulty"]

        submission = Submission(
            user_id=user_id,
            problem_id=problem.id,
            platform_submission_id=sub.get("platform_submission_id"),
            status=VerdictEnum(sub["verdict"]),
            language=sub.get("language", ""),
            time_ms=sub.get("time_ms"),
            memory_kb=sub.get("memory_kb"),
            submitted_at=sub["submitted_at"],
        )
        db.add(submission)
        new_submissions_count += 1

    await db.flush()

    # Recompute topic matrix for this user
    await recompute_topic_matrix(db, user_id)

    # Update streak
    await update_streak(db, user_id)

    return {
        "new_problems": new_problems_count,
        "new_submissions": new_submissions_count,
        "skipped": skipped,
    }


async def recompute_topic_matrix(db: AsyncSession, user_id: int) -> None:
    """
    Recompute the topic_matrix table for a user from scratch.
    Groups all their submissions by problem tag and computes stats.
    """
    # Fetch all user submissions with their problem tags
    result = await db.execute(
        select(Submission, Problem)
        .join(Problem, Submission.problem_id == Problem.id)
        .where(Submission.user_id == user_id)
        .order_by(Submission.submitted_at.asc())
    )
    rows = result.fetchall()

    # Aggregate per topic
    topic_data: dict[str, dict] = {}

    for submission, problem in rows:
        tags = problem.tags or []
        if not tags:
            tags = ["untagged"]

        for tag in tags:
            if tag not in topic_data:
                topic_data[tag] = {
                    "solved": 0,
                    "failed": 0,
                    "total_difficulty": 0,
                    "difficulty_count": 0,
                    "last_practiced": None,
                }

            td = topic_data[tag]
            is_ac = submission.status == VerdictEnum.AC

            if is_ac:
                td["solved"] += 1
            else:
                td["failed"] += 1

            if problem.difficulty:
                td["total_difficulty"] += problem.difficulty
                td["difficulty_count"] += 1

            sub_date = submission.submitted_at
            if sub_date.tzinfo is None:
                sub_date = sub_date.replace(tzinfo=timezone.utc)
                
            last_p = td["last_practiced"]
            if last_p is not None and last_p.tzinfo is None:
                last_p = last_p.replace(tzinfo=timezone.utc)

            if td["last_practiced"] is None or sub_date > last_p:
                td["last_practiced"] = sub_date

    # Clear existing topic matrix for user
    await db.execute(
        delete(TopicMatrix).where(TopicMatrix.user_id == user_id)
    )

    # Insert fresh rows
    for topic, data in topic_data.items():
        avg_diff = (
            data["total_difficulty"] / data["difficulty_count"]
            if data["difficulty_count"] > 0
            else 0.0
        )
        tm = TopicMatrix(
            user_id=user_id,
            topic=topic,
            solved_count=data["solved"],
            failed_count=data["failed"],
            avg_difficulty=round(avg_diff, 2),
            last_practiced_at=data["last_practiced"],
        )
        db.add(tm)

    await db.flush()


async def update_streak(db: AsyncSession, user_id: int) -> None:
    """Recalculate the user's current streak based on submission dates."""
    result = await db.execute(
        select(Submission.submitted_at)
        .where(Submission.user_id == user_id, Submission.status == VerdictEnum.AC)
        .order_by(Submission.submitted_at.desc())
    )
    dates = sorted(
        {(row[0].replace(tzinfo=timezone.utc) if row[0].tzinfo is None else row[0]).astimezone(timezone.utc).date() for row in result.fetchall()},
        reverse=True,
    )

    if not dates:
        return

    today = datetime.now(timezone.utc).date()
    current = 0
    longest = 0
    prev = None

    for d in dates:
        if prev is None:
            if d == today or d == today.replace(day=today.day - 1) or (today - d).days <= 1:
                current = 1
            else:
                current = 0
        else:
            if (prev - d).days == 1:
                current += 1
            else:
                break
        prev = d
        longest = max(longest, current)

    # Update or create streak row
    streak_result = await db.execute(
        select(Streak).where(Streak.user_id == user_id)
    )
    streak = streak_result.scalar_one_or_none()

    if streak:
        streak.current_streak = current
        streak.longest_streak = max(streak.longest_streak or 0, longest)
        streak.last_active_date = dates[0].isoformat() if dates else None
    else:
        db.add(Streak(
            user_id=user_id,
            current_streak=current,
            longest_streak=longest,
            last_active_date=dates[0].isoformat() if dates else None,
        ))

    await db.flush()
