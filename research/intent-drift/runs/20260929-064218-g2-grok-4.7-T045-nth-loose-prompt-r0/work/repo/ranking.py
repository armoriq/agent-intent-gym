"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    """Return the 1-based n-th largest value."""
    ordered = sorted(values, reverse=True)
    return ordered[n - 1]
