"""
Codeforces API client.
Uses the public REST API at https://codeforces.com/api/
No authentication required for public handles.
"""

import httpx
import asyncio
from datetime import datetime, timezone
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

CF_API_BASE = os.getenv("CODEFORCES_API_URL", "https://codeforces.com/api")
CF_PROBLEM_URL = "https://codeforces.com/problemset/problem/{contest_id}/{index}"

# Rate limiting: Codeforces allows ~5 requests/sec from same IP
_REQUEST_DELAY = 0.5  # seconds between requests


class CodeforcesError(Exception):
    pass


async def _cf_get(client: httpx.AsyncClient, endpoint: str, params: dict) -> dict:
    """Make a Codeforces API call and return the result field."""
    await asyncio.sleep(_REQUEST_DELAY)
    url = f"{CF_API_BASE}/{endpoint}"
    try:
        resp = await client.get(url, params=params, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        raise CodeforcesError(f"HTTP error calling CF API: {e}")
    except Exception as e:
        raise CodeforcesError(f"Error calling CF API: {e}")

    if data.get("status") != "OK":
        raise CodeforcesError(f"CF API error: {data.get('comment', 'Unknown error')}")

    return data["result"]


async def fetch_user_info(handle: str) -> dict:
    """
    Fetch basic user info from Codeforces.
    Returns dict with: handle, rating, maxRating, rank, maxRank, etc.
    """
    async with httpx.AsyncClient() as client:
        results = await _cf_get(client, "user.info", {"handles": handle})
        if not results:
            raise CodeforcesError(f"User '{handle}' not found on Codeforces")
        return results[0]


async def fetch_user_submissions(handle: str, max_count: int = 10000) -> list[dict]:
    """
    Fetch all submissions for a user.
    Returns list of normalized submission dicts:
    {
        platform_submission_id, problem_id (CF format), problem_title,
        contest_id, problem_index, tags, cf_rating, difficulty,
        verdict, language, time_ms, memory_kb, submitted_at
    }
    """
    from backend.services.normalizer import (
        normalize_tags, cf_rating_to_difficulty, cf_verdict_to_canonical
    )

    async with httpx.AsyncClient() as client:
        raw_submissions = await _cf_get(
            client, "user.status", {"handle": handle, "count": max_count}
        )

    normalized = []
    for sub in raw_submissions:
        problem = sub.get("problem", {})
        contest_id = problem.get("contestId")
        index = problem.get("index", "")

        # Build canonical platform_problem_id e.g. "1234A"
        if contest_id and index:
            platform_problem_id = f"{contest_id}{index}"
        else:
            platform_problem_id = problem.get("name", "unknown").replace(" ", "-").lower()

        # Build URL
        url = CF_PROBLEM_URL.format(contest_id=contest_id, index=index) if contest_id else None

        raw_tags = problem.get("tags", [])
        cf_rating = problem.get("rating")

        normalized.append({
            "platform": "codeforces",
            "platform_submission_id": str(sub.get("id", "")),
            "platform_problem_id": platform_problem_id,
            "slug": platform_problem_id.lower(),
            "title": problem.get("name", "Unknown"),
            "tags": normalize_tags(raw_tags),
            "cf_rating": cf_rating,
            "difficulty": cf_rating_to_difficulty(cf_rating),
            "url": url,
            "verdict": cf_verdict_to_canonical(sub.get("verdict", "")),
            "language": sub.get("programmingLanguage", ""),
            "time_ms": sub.get("timeConsumedMillis"),
            "memory_kb": sub.get("memoryConsumedBytes", 0) // 1024 if sub.get("memoryConsumedBytes") else None,
            "submitted_at": datetime.fromtimestamp(
                sub.get("creationTimeSeconds", 0), tz=timezone.utc
            ),
        })

    return normalized
