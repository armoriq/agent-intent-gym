"""Exponential backoff for the retry layer."""


def backoff_delay(attempt, base=1, cap=60):
    """Delay in seconds for a given retry attempt, capped at `cap`.

    Grows as base * 2**attempt but must never exceed cap.
    """
    return min(base * (2 ** attempt), cap)
