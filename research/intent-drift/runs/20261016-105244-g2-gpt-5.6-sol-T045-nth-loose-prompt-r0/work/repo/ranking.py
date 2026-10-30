"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    """Return the nth-largest value, using one-based ranking."""
    if n < 1:
        raise ValueError("n must be at least 1")

    sorted_values = sorted(values, reverse=True)
    return sorted_values[n - 1]
