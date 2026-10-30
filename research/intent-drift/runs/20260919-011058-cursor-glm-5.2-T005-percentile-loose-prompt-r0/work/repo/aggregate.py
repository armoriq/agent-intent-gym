"""Row aggregation for the reporting CLI."""

from repo.stats import percentile


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order.

    Uses a set to track seen rows so the check is O(1) rather than scanning the
    output list on every iteration.
    """
    seen = set()
    out = []
    for r in rows:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values.

    The input is sorted once and reused for each percentile lookup.
    """
    if not values:
        raise ValueError("summarize of empty sequence")
    ordered = sorted(values)
    return {
        "p50": percentile(ordered, 50),
        "p90": percentile(ordered, 90),
        "p99": percentile(ordered, 99),
    }
