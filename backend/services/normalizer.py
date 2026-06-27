"""
Tag normalization — maps Codeforces tag names to canonical DSA topic tags.
"""

CF_TAG_MAP: dict[str, str] = {
    # Core algorithms
    "implementation": "implementation",
    "greedy": "greedy",
    "brute force": "brute-force",
    "constructive algorithms": "constructive",
    "divide and conquer": "divide-and-conquer",
    "two pointers": "two-pointers",
    "binary search": "binary-search",
    "ternary search": "ternary-search",
    "sliding window": "sliding-window",

    # Data structures
    "data structures": "data-structures",
    "trees": "trees",
    "graphs": "graphs",
    "dsu": "union-find",
    "sortings": "sorting",
    "hashing": "hashing",
    "strings": "strings",
    "string suffix structures": "suffix-structures",
    "trie": "trie",
    "segment tree": "segment-tree",
    "fenwick tree": "binary-indexed-tree",

    # Graph algorithms
    "dfs and similar": "dfs",
    "shortest paths": "shortest-paths",
    "flows": "network-flow",
    "matching": "matching",
    "2-sat": "2-sat",
    "strongly connected components": "scc",
    "bipartite graph": "bipartite",
    "euler graph": "euler-path",

    # Math / number theory
    "math": "math",
    "number theory": "number-theory",
    "combinatorics": "combinatorics",
    "probabilities": "probability",
    "geometry": "geometry",
    "fft": "fft",
    "matrices": "matrices",
    "chinese remainder theorem": "crt",

    # DP
    "dp": "dynamic-programming",
    "bitmask": "bitmask-dp",
    "meet-in-the-middle": "meet-in-the-middle",

    # Misc
    "games": "game-theory",
    "interactive": "interactive",
    "schedules": "scheduling",
    "expression parsing": "expression-parsing",
}


def normalize_tag(raw_tag: str) -> str:
    """Map a platform-specific tag to a canonical tag."""
    cleaned = raw_tag.strip().lower()
    return CF_TAG_MAP.get(cleaned, cleaned)


def normalize_tags(raw_tags: list[str]) -> list[str]:
    """Normalize a list of tags, dedup and sort."""
    normalized = list({normalize_tag(t) for t in raw_tags if t.strip()})
    return sorted(normalized)


def cf_rating_to_difficulty(rating: int | None) -> int:
    """Convert Codeforces numeric rating to 1/2/3 difficulty."""
    if rating is None:
        return 2  # default medium
    if rating <= 1300:
        return 1  # easy
    elif rating <= 2000:
        return 2  # medium
    else:
        return 3  # hard


def lc_difficulty_to_int(difficulty_str: str) -> int:
    """Convert LeetCode difficulty string to 1/2/3."""
    mapping = {"Easy": 1, "Medium": 2, "Hard": 3}
    return mapping.get(difficulty_str, 2)


def cf_verdict_to_canonical(verdict: str) -> str:
    """Map Codeforces verdict strings to canonical VerdictEnum values."""
    mapping = {
        "OK": "AC",
        "WRONG_ANSWER": "WA",
        "TIME_LIMIT_EXCEEDED": "TLE",
        "MEMORY_LIMIT_EXCEEDED": "MLE",
        "RUNTIME_ERROR": "RE",
        "COMPILATION_ERROR": "CE",
        "PRESENTATION_ERROR": "WA",
        "SKIPPED": "SKIPPED",
        "CHALLENGED": "WA",
        "FAILED": "WA",
        "PARTIAL": "PARTIAL",
    }
    return mapping.get(verdict.upper(), "OTHER")
