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
    # Nearest-rank method: rank = ceil(p/100 * n), 1-indexed. Clamp to >= 1 so
    # p=0 yields the minimum instead of wrapping to the end of the list.
    rank = max(1, math.ceil(p / 100 * n))
    return ordered[rank - 1]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
