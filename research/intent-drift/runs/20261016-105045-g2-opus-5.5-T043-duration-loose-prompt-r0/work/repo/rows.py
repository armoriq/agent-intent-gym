"""Row helpers for the reporting module."""
from repo.timefmt import format_hms


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def hms_summary(secs_list):
    """Return a small summary block for a column of numbers."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {"count": len(secs_list), "formatted": [format_hms(s) for s in secs_list]}
