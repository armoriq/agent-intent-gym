"""Row aggregation for the reporting CLI."""
from repo.stats import percentiles


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    seen = set()
    for row in rows:
        try:
            if row in seen:
                continue
            seen.add(row)
        except TypeError:
            # Report rows may contain unhashable values such as lists or dicts.
            if row in out:
                continue
        out.append(row)
    return out


def summarize(values):
    """Return a p50/p90/p99 summary for a column of values."""
    names = ("p50", "p90", "p99")
    return dict(zip(names, percentiles(values, (50, 90, 99))))
