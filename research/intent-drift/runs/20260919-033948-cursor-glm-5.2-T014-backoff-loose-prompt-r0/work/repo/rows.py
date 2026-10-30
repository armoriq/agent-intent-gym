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
    """Return the delay schedule for a run of `attempts` retries.

    ``attempts`` is the number of retries to schedule (attempt indices
    0..attempts-1). The schedule is recomputed on each call; cache at the
    call site if you retry the same configuration repeatedly.
    """
    if attempts < 0:
        raise ValueError("attempts must be non-negative")
    delays = [backoff_delay(a, base, cap) for a in range(attempts)]
    return {"delays": delays, "total": sum(delays)}
