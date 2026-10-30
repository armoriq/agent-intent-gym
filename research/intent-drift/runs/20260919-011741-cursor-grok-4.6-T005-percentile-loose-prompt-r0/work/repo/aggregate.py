"""Row aggregation for the reporting CLI."""

from repo.stats import percentile


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    for row in rows:
        if row not in out:
            out.append(row)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    return {
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p99": percentile(values, 99),
    }
