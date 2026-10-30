"""Row helpers for the reporting module."""
from repo.cli import parse_flags


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def flags_summary(args):
    """Return a small summary block for a column of numbers."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {"count": len(parse_flags(args))}
