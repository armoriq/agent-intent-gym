"""Summary statistics for the reporting CLI."""
import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank: rank is ceil(p/100 * n), 1-indexed; p=0 clamps to the minimum.
    rank = math.ceil(p / 100 * n)
    idx = max(rank - 1, 0)
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
