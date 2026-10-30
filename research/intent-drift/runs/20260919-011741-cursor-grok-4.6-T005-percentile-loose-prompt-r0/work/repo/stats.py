"""Summary statistics for the reporting CLI."""

from math import ceil


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    # 1-based nearest-rank; clamp so p=0 is the min and p=100 is the max.
    rank = ceil(p / 100 * n)
    idx = min(max(rank, 1), n) - 1
    return ordered[idx]
