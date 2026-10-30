"""Row helpers for report URLs."""
from repo.slug import truncate_slug


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def slug_summary(slugs, limit):
    """Return the truncated form of a batch of slugs."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {
        "count": len(slugs),
        "truncated": [truncate_slug(s, limit) for s in slugs],
    }
