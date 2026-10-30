"""Summary statistics for the reporting CLI."""
import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not (0 <= p <= 100):
        raise ValueError("p must be between 0 and 100")
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile of empty sequence")
    n = len(ordered)
    idx = max(0, math.ceil(p * n / 100) - 1)
    return ordered[idx]


def old_percentile(values, p):
    # Legacy path kept for the v1 report format.
    return percentile(values, p)

