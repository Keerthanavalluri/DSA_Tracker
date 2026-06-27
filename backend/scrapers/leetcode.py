"""
LeetCode scraper using Playwright to bypass Cloudflare.
Uses in-browser fetch() to hit LeetCode's GraphQL API directly.
Requires a valid LEETCODE_SESSION cookie from the user's browser.
"""

import json
import logging
from playwright.async_api import async_playwright
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

LEETCODE_GQL_URL = "https://leetcode.com/graphql"

SUBMISSIONS_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
  }
}
"""

PROBLEM_TAGS_QUERY = """
query questionTags($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    difficulty
    topicTags {
      name
    }
  }
}
"""

# Maps LeetCode tag names to our canonical tag names
LC_TAG_MAP = {
    "Array": "arrays",
    "String": "strings",
    "Hash Table": "hashing",
    "Dynamic Programming": "dp",
    "Math": "math",
    "Sorting": "sorting",
    "Greedy": "greedy",
    "Depth-First Search": "dfs",
    "Breadth-First Search": "bfs",
    "Binary Search": "binary-search",
    "Tree": "trees",
    "Binary Tree": "trees",
    "Graph": "graphs",
    "Linked List": "linked-list",
    "Stack": "stacks",
    "Queue": "queues",
    "Two Pointers": "two-pointers",
    "Sliding Window": "sliding-window",
    "Divide and Conquer": "divide-and-conquer",
    "Backtracking": "backtracking",
    "Bit Manipulation": "bitmasks",
    "Heap (Priority Queue)": "heaps",
    "Simulation": "implementation",
    "Trie": "trie",
    "Segment Tree": "segment-tree",
    "Union Find": "dsu",
    "Design": "implementation",
    "Monotonic Stack": "stacks",
    "Recursion": "recursion",
    "Combinatorics": "combinatorics",
    "Geometry": "geometry",
    "Number Theory": "number-theory",
    "Game Theory": "game-theory",
}


def normalize_lc_tags(raw_tags: list[str]) -> list[str]:
    """Translate LeetCode tags to canonical tag names."""
    seen = set()
    result = []
    for tag in raw_tags:
        canonical = LC_TAG_MAP.get(tag, tag.lower().replace(" ", "-"))
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


async def fetch_leetcode_submissions(
    username: str, session_cookie: str, limit: int = 50
) -> list[dict]:
    """
    Uses Playwright to fetch LeetCode submissions via in-browser fetch.
    This bypasses Cloudflare because the browser context is trusted.
    Requires a valid LEETCODE_SESSION cookie.

    Returns a list of dicts compatible with sync_submissions():
      - platform, platform_problem_id, slug, title, difficulty, tags,
        platform_submission_id, verdict, submitted_at, language
    """
    submissions_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Set the auth cookie
        await context.add_cookies([
            {
                "name": "LEETCODE_SESSION",
                "value": session_cookie,
                "domain": ".leetcode.com",
                "path": "/",
            }
        ])

        page = await context.new_page()

        # Navigate to leetcode to establish CF clearance
        try:
            await page.goto(
                "https://leetcode.com/", wait_until="commit", timeout=15000
            )
        except Exception as e:
            logger.warning(f"[WARN] LeetCode initial navigation issue (non-fatal): {e}")

        payload = {
            "query": SUBMISSIONS_QUERY,
            "variables": {"username": username, "limit": limit},
        }

        # Use page.evaluate to run fetch() inside the browser context
        js_fetch = f"""
        async () => {{
            const res = await fetch("{LEETCODE_GQL_URL}", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({json.dumps(payload)})
            }});
            return await res.json();
        }}
        """

        try:
            res_json = await page.evaluate(js_fetch)

            if not res_json or "data" not in res_json:
                logger.error("[ERROR] LeetCode GQL returned no data. Cookie may be expired.")
                await browser.close()
                return []

            ac_list = res_json["data"].get("recentAcSubmissionList") or []

            if not ac_list:
                logger.info("[OK] LeetCode returned 0 AC submissions for %s", username)
                await browser.close()
                return []

            # Fetch tags for each unique problem
            unique_slugs = {sub["titleSlug"] for sub in ac_list}
            tags_cache: dict[str, dict] = {}

            for slug in unique_slugs:
                tag_payload = {
                    "query": PROBLEM_TAGS_QUERY,
                    "variables": {"titleSlug": slug},
                }
                tag_js = f"""
                async () => {{
                    const res = await fetch("{LEETCODE_GQL_URL}", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({json.dumps(tag_payload)})
                    }});
                    return await res.json();
                }}
                """
                try:
                    tag_res = await page.evaluate(tag_js)
                    tags_cache[slug] = tag_res.get("data", {}).get("question", {})
                except Exception:
                    tags_cache[slug] = {}
                # Rate-limit: 500ms between requests
                await page.wait_for_timeout(500)

            # Assemble into sync-compatible format
            for sub in ac_list:
                slug = sub["titleSlug"]
                q_info = tags_cache.get(slug, {})

                diff_str = q_info.get("difficulty", "Medium")
                diff_num = 1 if diff_str == "Easy" else (3 if diff_str == "Hard" else 2)

                raw_tags = [t["name"] for t in q_info.get("topicTags", [])]
                canonical_tags = normalize_lc_tags(raw_tags)

                submissions_data.append({
                    "platform": "leetcode",
                    "platform_problem_id": slug,
                    "platform_submission_id": f"lc-{sub['id']}",
                    "slug": slug,
                    "title": sub["title"],
                    "difficulty": diff_num,
                    "tags": canonical_tags,
                    "url": f"https://leetcode.com/problems/{slug}/",
                    "verdict": "AC",
                    "submitted_at": datetime.fromtimestamp(
                        int(sub["timestamp"]), tz=timezone.utc
                    ),
                    "language": "unknown",
                })

        except Exception as e:
            logger.error(f"[ERROR] LeetCode fetch failed: {e}")

        await browser.close()

    logger.info(
        "[OK] LeetCode scraper fetched %d submissions for %s",
        len(submissions_data),
        username,
    )
    return submissions_data
