"""Summary statistics for the reporting CLI."""

import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    Uses the nearest-rank method: the rank is ``ceil(p / 100 * n)`` (1-indexed)
    and clamped to ``[1, n]``. With this definition ``p=0`` returns the minimum
    and ``p=100`` returns the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError(f"percentile must be in [0, 100], got {p!r}")

    ordered = sorted(values)
    n = len(ordered)

    # Nearest-rank: rank is 1-indexed, ceil(p/100 * n), clamped to [1, n].
    rank = math.ceil(p / 100 * n)
    if rank < 1:
        rank = 1
    elif rank > n:
        rank = n
    return ordered[rank - 1]
