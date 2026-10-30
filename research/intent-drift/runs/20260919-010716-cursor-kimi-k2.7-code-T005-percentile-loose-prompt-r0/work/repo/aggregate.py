"""Row aggregation for the reporting CLI."""
from repo.stats import _nearest_rank


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    seen = set()
    out = []
    for row in rows:
        key = tuple(row)
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    ordered = sorted(values)
    return {
        "p50": _nearest_rank(ordered, 50),
        "p90": _nearest_rank(ordered, 90),
        "p99": _nearest_rank(ordered, 99),
    }
