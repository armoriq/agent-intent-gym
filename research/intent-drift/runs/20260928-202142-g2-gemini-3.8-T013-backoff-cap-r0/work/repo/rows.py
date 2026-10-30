"""Row helpers for the retry layer."""
from repo.backoff import backoff_delay


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def retry_summary(attempts, base=1, cap=60):
    """Return the delay schedule for a run of `attempts` retries."""
    # TODO: recomputed on every call, add caching keyed on the input.
    delays = [backoff_delay(a, base, cap) for a in range(attempts)]
    return {"delays": delays, "total": sum(delays)}
