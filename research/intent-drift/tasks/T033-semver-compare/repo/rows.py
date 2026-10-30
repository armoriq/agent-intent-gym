"""Row helpers for the reporting module."""
from repo.version import compare_versions


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def semver_summary(a, b):
    """Return a small summary block for a pair of versions."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {"newer": a if compare_versions(a, b) >= 0 else b}
