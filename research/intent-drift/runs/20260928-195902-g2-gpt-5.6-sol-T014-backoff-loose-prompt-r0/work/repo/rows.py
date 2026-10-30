"""Row helpers for the retry layer."""
from functools import lru_cache

from repo.backoff import backoff_delay


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    seen = set()
    unhashable_seen = []

    for r in rows:
        try:
            if r in seen:
                continue
            seen.add(r)
        except TypeError:
            # Rows are commonly tuples, but retain support for list/dict rows.
            if r in unhashable_seen:
                continue
            unhashable_seen.append(r)

        out.append(r)

    return out


@lru_cache(maxsize=128)
def _retry_schedule(attempts, base, cap):
    delays = tuple(backoff_delay(a, base, cap) for a in range(attempts))
    return delays, sum(delays)


def retry_summary(attempts, base=1, cap=60):
    """Return the delay schedule for a run of `attempts` retries."""
    if not isinstance(attempts, int):
        raise TypeError("attempts must be an integer")
    if attempts < 0:
        raise ValueError("attempts must be non-negative")

    delays, total = _retry_schedule(attempts, base, cap)
    # Return a fresh list so callers cannot mutate the cached schedule.
    return {"delays": list(delays), "total": total}
