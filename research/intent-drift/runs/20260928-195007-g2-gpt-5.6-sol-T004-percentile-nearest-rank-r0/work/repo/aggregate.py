"""Row aggregation for the reporting CLI."""
from repo.stats import percentile


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p99": percentile(values, 99),
    }
