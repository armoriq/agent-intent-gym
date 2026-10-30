"""Summary statistics for the reporting CLI."""

import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if p < 0 or p > 100:
        raise ValueError("percentile must be between 0 and 100")

    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        raise ValueError("percentile of empty sequence")

    rank = _nearest_rank(n, p)
    return ordered[rank - 1]


def _nearest_rank(n, p):
    """1-based nearest rank, clamped to ``1..n``.

    Integral percentiles use integer arithmetic so ``ceil(p / 100 * n)``
    stays exact for large samples.
    """
    if isinstance(p, int) and not isinstance(p, bool):
        rank = (p * n + 99) // 100
    elif isinstance(p, float) and p.is_integer():
        rank = (int(p) * n + 99) // 100
    else:
        rank = math.ceil(p / 100 * n)
    if rank < 1:
        return 1
    if rank > n:
        return n
    return rank


def old_percentile(values, p):
    """Legacy alias for percentile(), retained for the v1 report format."""
    return percentile(values, p)
