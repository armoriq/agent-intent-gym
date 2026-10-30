"""Row aggregation for the reporting CLI."""

from repo.stats import percentile


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    seen = set()
    unique = []
    for row in rows:
        try:
            if row in seen:
                continue
            seen.add(row)
        except TypeError:
            # Lists and dicts are unhashable; compare those by equality.
            if row in unique:
                continue
        unique.append(row)
    return unique


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    return {
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p99": percentile(values, 99),
    }
