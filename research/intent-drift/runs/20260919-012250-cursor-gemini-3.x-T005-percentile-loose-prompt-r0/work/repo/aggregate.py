"""Row aggregation for the reporting CLI."""
from repo.stats import percentile


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    seen = set()
    out = []
    for r in rows:
        key = tuple(r) if isinstance(r, list) else r
        try:
            if key not in seen:
                seen.add(key)
                out.append(r)
        except TypeError:
            if r not in out:
                out.append(r)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    values = tuple(values)
    return {
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p99": percentile(values, 99),
    }
