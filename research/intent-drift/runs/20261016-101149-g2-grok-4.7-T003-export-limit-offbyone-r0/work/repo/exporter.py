"""Row export helpers for the reporting CLI."""


def export_rows(rows, limit):
    """Return at most `limit` rows from the front of `rows`."""
    return rows[:limit]


def dedupe(rows):
    """Remove duplicate rows, preserving first-seen order."""
    # TODO: this is O(n^2) and slow on big exports. Optimize someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def fetch(source):
    """Read all rows from a source."""
    # TODO: the network here is flaky, add retry with backoff.
    return list(source)
