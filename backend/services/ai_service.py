"""
AI service — Grok API via OpenAI-compatible SDK.
Sends precomputed topicMatrix, receives structured JSON recommendations.
"""

import json
import os
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from backend.models.topic_matrix import TopicMatrix, AIRecommendation
from backend.models.study import Streak
from backend.models.submission import Submission
from dotenv import load_dotenv

load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3")
RECOMMENDATION_TTL_HOURS = 24

_client = AsyncOpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1",
)

SYSTEM_PROMPT = """You are an expert competitive programming coach.
You analyze a coder's topic performance data and return structured JSON advice.
ALWAYS respond with valid JSON only, no markdown, no explanation outside the JSON.
The JSON must have exactly these fields:
{
  "weakTopics": ["topic1", "topic2"],
  "strengthTopics": ["topic3", "topic4"],
  "suggestedProblems": [
    {"slug": "problem-slug", "platform": "LC|CF", "title": "Problem Title", "reason": "why this problem"}
  ],
  "studyHints": ["hint1", "hint2", "hint3"],
  "weeklyGoal": "A specific, actionable weekly goal"
}"""

USER_PROMPT_TEMPLATE = """Analyze this competitive programmer's performance data and give actionable advice:

Handle: {username}
Total Solved: {total_solved}
Current Streak: {streak} days

Topic Performance Matrix:
{topic_matrix_json}

Focus on:
1. Identifying the 2-3 weakest topics (high fail rate + low solved count)
2. Suggesting 3-5 specific problems to practice (with reasons)
3. Giving 3 concrete study hints personalized to their weak areas
4. Setting a realistic weekly goal

Return ONLY valid JSON matching the required schema."""


async def get_or_generate_recommendation(
    db: AsyncSession,
    user_id: int,
    username: str,
    force_refresh: bool = False,
) -> dict:
    """
    Return cached recommendation if < 24h old, otherwise generate a fresh one.
    """
    # Check cache
    if not force_refresh:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=RECOMMENDATION_TTL_HOURS)
        cached = await db.execute(
            select(AIRecommendation)
            .where(
                AIRecommendation.user_id == user_id,
                AIRecommendation.generated_at >= cutoff,
            )
            .order_by(AIRecommendation.generated_at.desc())
            .limit(1)
        )
        rec = cached.scalar_one_or_none()
        if rec:
            return _rec_to_dict(rec)

    # Build topicMatrix
    topic_result = await db.execute(
        select(TopicMatrix)
        .where(TopicMatrix.user_id == user_id)
        .order_by(TopicMatrix.solved_count.asc())
        .limit(30)  # Top 30 topics max
    )
    topics = topic_result.scalars().all()

    if not topics:
        return {"error": "No data yet. Sync your Codeforces account first."}

    topic_matrix_data = {}
    for tm in topics:
        topic_matrix_data[tm.topic] = {
            "solved": tm.solved_count,
            "failed": tm.failed_count,
            "avgDifficulty": tm.avg_difficulty,
            "lastPracticed": tm.last_practiced_at.strftime("%Y-%m-%d") if tm.last_practiced_at else "never",
        }

    # Get streak
    streak_result = await db.execute(
        select(Streak).where(Streak.user_id == user_id)
    )
    streak_obj = streak_result.scalar_one_or_none()
    streak_days = streak_obj.current_streak if streak_obj else 0

    # Count total solved
    total_solved = sum(t.solved_count for t in topics)

    # Call Grok
    prompt = USER_PROMPT_TEMPLATE.format(
        username=username,
        total_solved=total_solved,
        streak=streak_days,
        topic_matrix_json=json.dumps(topic_matrix_data, indent=2),
    )

    try:
        response = await _client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        raw_text = response.choices[0].message.content.strip()

        # Parse JSON
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        parsed = json.loads(raw_text)

    except json.JSONDecodeError:
        parsed = {
            "weakTopics": [],
            "strengthTopics": [],
            "suggestedProblems": [],
            "studyHints": ["Unable to parse AI response. Please try again."],
            "weeklyGoal": "Keep practicing!",
        }
    except Exception as e:
        return {"error": f"AI service error: {str(e)}"}

    # Cache in DB
    rec = AIRecommendation(
        user_id=user_id,
        weak_topics=json.dumps(parsed.get("weakTopics", [])),
        strength_topics=json.dumps(parsed.get("strengthTopics", [])),
        suggested_problems=json.dumps(parsed.get("suggestedProblems", [])),
        study_hints=json.dumps(parsed.get("studyHints", [])),
        weekly_goal=parsed.get("weeklyGoal", ""),
        raw_response=raw_text if isinstance(raw_text, str) else json.dumps(parsed),
    )
    db.add(rec)
    await db.flush()

    return _rec_to_dict(rec)


def _rec_to_dict(rec: AIRecommendation) -> dict:
    def safe_parse(s):
        try:
            return json.loads(s) if s else []
        except Exception:
            return []

    return {
        "generatedAt": rec.generated_at.isoformat() if rec.generated_at else None,
        "weakTopics": safe_parse(rec.weak_topics),
        "strengthTopics": safe_parse(rec.strength_topics),
        "suggestedProblems": safe_parse(rec.suggested_problems),
        "studyHints": safe_parse(rec.study_hints),
        "weeklyGoal": rec.weekly_goal or "",
    }


PLAN_SYSTEM_PROMPT = """You are an expert competitive programming coach.
You generate structured, multi-day study plans based on a coder's topic performance data.
ALWAYS respond with valid JSON only, no markdown, no explanation outside the JSON.
The JSON must have this exact schema:
{
  "plan": [
    {
      "day": 1,
      "focus": "Topic Name (e.g. Dynamic Programming)",
      "tasks": [
        {"title": "Problem Title or Concept", "platform": "LC|CF", "reason": "why this task"}
      ]
    }
  ]
}"""

PLAN_USER_PROMPT = """Create a {days}-day study plan for this competitive programmer:

Handle: {username}
Total Solved: {total_solved}
Current Streak: {streak} days

Topic Performance Matrix (focus on weak topics):
{topic_matrix_json}

Return ONLY valid JSON matching the schema."""

from backend.models.study_plan import StudyPlan

async def generate_study_plan(
    db: AsyncSession,
    user_id: int,
    username: str,
    days: int
) -> dict:
    # Build topicMatrix
    topic_result = await db.execute(
        select(TopicMatrix)
        .where(TopicMatrix.user_id == user_id)
        .order_by(TopicMatrix.solved_count.asc())
        .limit(30)
    )
    topics = topic_result.scalars().all()

    if not topics:
        return {"error": "No data yet. Sync an account first."}

    topic_matrix_data = {}
    for tm in topics:
        topic_matrix_data[tm.topic] = {
            "solved": tm.solved_count,
            "failed": tm.failed_count,
            "avgDifficulty": tm.avg_difficulty,
        }

    # Get streak
    streak_result = await db.execute(select(Streak).where(Streak.user_id == user_id))
    streak_obj = streak_result.scalar_one_or_none()
    streak_days = streak_obj.current_streak if streak_obj else 0
    total_solved = sum(t.solved_count for t in topics)

    prompt = PLAN_USER_PROMPT.format(
        days=days,
        username=username,
        total_solved=total_solved,
        streak=streak_days,
        topic_matrix_json=json.dumps(topic_matrix_data, indent=2),
    )

    try:
        response = await _client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        raw_text = response.choices[0].message.content.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        parsed = json.loads(raw_text)

    except Exception as e:
        return {"error": f"AI service error: {str(e)}"}

    plan = StudyPlan(
        user_id=user_id,
        duration_days=days,
        plan_data=json.dumps(parsed),
    )
    db.add(plan)
    await db.flush()

    return {
        "generatedAt": plan.generated_at.isoformat() if plan.generated_at else None,
        "durationDays": plan.duration_days,
        "plan": parsed.get("plan", [])
    }

