"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    """Return the nth-largest value (n=1 is the maximum)."""
    if not 1 <= n <= len(values):
        raise ValueError(f"n must be between 1 and {len(values)}, got {n}")
    return sorted(values, reverse=True)[n - 1]
