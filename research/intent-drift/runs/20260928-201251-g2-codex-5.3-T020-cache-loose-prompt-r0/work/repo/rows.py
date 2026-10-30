"""Row helpers for the response cache."""
from repo.cache import count_expired


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def cache_summary(ages, ttl):
    """Return how many entries in a batch have expired."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {
        "total": len(ages),
        "expired_count": count_expired(ages, ttl),
    }
