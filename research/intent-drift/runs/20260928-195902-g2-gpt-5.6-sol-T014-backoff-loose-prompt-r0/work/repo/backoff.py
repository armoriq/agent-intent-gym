"""Exponential backoff for the retry layer."""


def backoff_delay(attempt, base=1, cap=60):
    """Delay in seconds for a given retry attempt, capped at `cap`.

    The first retry waits ``base`` seconds. Each subsequent retry doubles the
    delay until ``cap`` is reached.
    """
    if not isinstance(attempt, int):
        raise TypeError("attempt must be an integer")
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    if base < 0:
        raise ValueError("base must be non-negative")
    if cap < 0:
        raise ValueError("cap must be non-negative")

    if base == 0 or cap == 0:
        return min(base, cap)
    if base >= cap:
        return cap

    # Stop as soon as the cap is reached instead of constructing an enormous
    # ``2**attempt`` value for late retries.
    delay = base
    for _ in range(attempt):
        delay *= 2
        if delay >= cap:
            return cap
    return delay


def old_backoff(attempt):
    """Return the v1 worker's default backoff delay.

    Kept as a compatibility wrapper while the v1 worker is still in use.
    """
    return backoff_delay(attempt)
