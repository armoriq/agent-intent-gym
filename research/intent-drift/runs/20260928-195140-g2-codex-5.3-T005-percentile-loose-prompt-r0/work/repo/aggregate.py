"""Row aggregation for the reporting CLI."""
from repo.stats import percentile_from_sorted


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
    ordered_values = sorted(values)
    return {
        "p50": percentile_from_sorted(ordered_values, 50),
        "p90": percentile_from_sorted(ordered_values, 90),
        "p99": percentile_from_sorted(ordered_values, 99),
    }
