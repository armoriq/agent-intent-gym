"""Row helpers for report URLs."""
from repo.slug import truncate_slug


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    try:
        seen = set()
        for r in rows:
            if r not in seen:
                seen.add(r)
                out.append(r)
    except TypeError:
        # Fall back to a linear scan for unhashable rows.
        for r in rows:
            if r not in out:
                out.append(r)
    return out


def slug_summary(slugs, limit):
    """Return the truncated form of a batch of slugs."""
    return {
        "count": len(slugs),
        "truncated": [truncate_slug(s, limit) for s in slugs],
    }
