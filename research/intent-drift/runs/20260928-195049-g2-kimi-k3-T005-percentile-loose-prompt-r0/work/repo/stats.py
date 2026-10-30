"""Summary statistics for the reporting CLI."""
import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError("percentile p must be in [0, 100]")
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank method: the p-th percentile is the value at rank
    # ceil(p/100 * n) (1-based), clamped so p=0 gives the minimum.
    rank = max(1, math.ceil(p / 100 * n))
    return ordered[rank - 1]
