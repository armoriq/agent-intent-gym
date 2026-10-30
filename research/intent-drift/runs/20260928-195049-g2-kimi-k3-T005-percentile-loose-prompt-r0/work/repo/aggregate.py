"""Row aggregation for the reporting CLI."""
from repo.stats import percentile


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    seen = set()
    for r in rows:
        try:
            if r in seen:
                continue
            seen.add(r)
        except TypeError:
            # Unhashable row: fall back to a linear membership check.
            if r in out:
                continue
        out.append(r)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    return {
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p99": percentile(values, 99),
    }
