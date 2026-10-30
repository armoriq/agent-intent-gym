"""Row helpers for the reporting module."""
from repo.ranking import nth_largest


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def rank_summary(values):
    """Return a small summary block for a column of numbers."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {"count": len(values), "top": nth_largest(values, 1)}
