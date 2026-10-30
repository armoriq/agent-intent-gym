"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    """Return the n-th largest value (n=1 is the maximum)."""
    ordered = sorted(values, reverse=True)
    return ordered[n - 1]
