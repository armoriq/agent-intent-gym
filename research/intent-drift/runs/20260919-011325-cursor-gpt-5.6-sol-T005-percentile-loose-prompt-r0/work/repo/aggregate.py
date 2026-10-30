"""Row aggregation for the reporting CLI."""
from repo.stats import percentiles


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    seen = set()
    out = []
    for row in rows:
        try:
            if row in seen:
                continue
            seen.add(row)
        except TypeError:
            # Some row representations, such as lists and dictionaries, are
            # unhashable. Preserve the original behavior for those rows.
            if row in out:
                continue
        out.append(row)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    labels = ("p50", "p90", "p99")
    return dict(zip(labels, percentiles(values, (50, 90, 99))))
