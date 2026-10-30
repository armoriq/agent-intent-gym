"""Summary statistics for the reporting CLI."""

import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    Uses the nearest-rank method: the rank is ``ceil(p / 100 * n)`` (1-indexed)
    and clamped to ``[1, n]``, so ``p=0`` returns the minimum and ``p=100`` the
    maximum. An empty input raises ``ValueError``.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError("percentile must be in [0, 100]")

    ordered = sorted(values)
    n = len(ordered)
    rank = math.ceil(p / 100 * n)
    # Clamp into the valid 1-indexed range to handle p=0 and floating drift.
    rank = max(1, min(rank, n))
    return ordered[rank - 1]
