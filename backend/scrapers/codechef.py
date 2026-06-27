"""
CodeChef scraper using their public API + GraphQL endpoint.
Fetches user submission history and normalises into canonical schema.
"""
import httpx
import asyncio
from typing import Optional

CODECHEF_API = "https://www.codechef.com"

# Canonical tag mapping for CodeChef problem categories
CODECHEF_TAG_MAP = {
    "dynamic programming": "dynamic-programming",
    "dp": "dynamic-programming",
    "graphs": "graphs",
    "graph theory": "graphs",
    "trees": "trees",
    "binary search": "binary-search",
    "greedy": "greedy",
    "math": "math",
    "mathematics": "math",
    "number theory": "math",
    "sorting": "sorting",
    "string algorithms": "strings",
    "strings": "strings",
    "data structures": "data-structures",
    "segment tree": "data-structures",
    "fenwick tree": "data-structures",
    "bit manipulation": "bit-manipulation",
    "two pointers": "two-pointers",
    "recursion": "recursion",
    "backtracking": "backtracking",
    "geometry": "geometry",
    "combinatorics": "math",
    "divide and conquer": "divide-and-conquer",
}

# CodeChef difficulty from level
DIFFICULTY_MAP = {
    "beginner": 1,
    "easy": 1,
    "medium": 2,
    "hard": 3,
    "challenge": 3,
    "extcontest": 2,
}


def normalize_cc_tag(raw: str) -> str:
    clean = raw.strip().lower()
    return CODECHEF_TAG_MAP.get(clean, clean)


def normalize_cc_difficulty(level: Optional[str]) -> int:
    if not level:
        return 2
    return DIFFICULTY_MAP.get(level.strip().lower(), 2)


async def fetch_user_info(username: str) -> dict:
    """Fetch basic CodeChef user info from their public API."""
    url = f"{CODECHEF_API}/api/user/{username}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "OK":
        raise ValueError(f"CodeChef user '{username}' not found")

    return data


async def fetch_submissions(username: str, pages: int = 5) -> list[dict]:
    """
    Fetch recent accepted submissions for a CodeChef user.
    Uses their /api/submission endpoint (paginated).
    Returns a list of normalised submission dicts.
    """
    submissions = []

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for page in range(1, pages + 1):
            url = f"{CODECHEF_API}/api/submission/{username}?page={page}&result=AC"
            try:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                })
                if resp.status_code != 200:
                    break
                data = resp.json()
            except Exception:
                break

            raw_subs = data.get("data", {}).get("content", [])
            if not raw_subs:
                break

            for s in raw_subs:
                submissions.append({
                    "platform": "codechef",
                    "problem_id": s.get("problemCode", ""),
                    "problem_title": s.get("problemName", s.get("problemCode", "")),
                    "status": "solved",  # we requested AC only
                    "language": s.get("language", ""),
                    "submitted_at": s.get("date", ""),
                    "difficulty": normalize_cc_difficulty(s.get("problemDifficulty")),
                    "tags": [],  # CodeChef submission API doesn't include tags inline
                })

            # Rate limiting
            await asyncio.sleep(0.5)

    return submissions


async def fetch_problem_tags(problem_code: str) -> list[str]:
    """Fetch tags for a single problem via CodeChef's problem detail API."""
    url = f"{CODECHEF_API}/api/problem/{problem_code}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                return []
            data = resp.json()
        raw_tags = data.get("problemDetails", {}).get("tags", [])
        return [normalize_cc_tag(t) for t in raw_tags if t]
    except Exception:
        return []
