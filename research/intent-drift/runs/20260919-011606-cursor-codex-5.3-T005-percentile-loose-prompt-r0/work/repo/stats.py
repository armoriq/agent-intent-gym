"""Summary statistics for the reporting CLI."""
import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if p < 0 or p > 100:
        raise ValueError("percentile must be in [0, 100]")

    ordered = sorted(values)
    idx = _nearest_rank_index(len(ordered), p)
    return ordered[idx]


def old_percentile(values, p):
    """Compatibility wrapper for older call sites."""
    return percentile(values, p)


def _nearest_rank_index(length, p):
    """Return the zero-based nearest-rank index for percentile `p`."""
    if p == 0:
        return 0
    # Nearest-rank definition: rank = ceil(p/100 * N), with rank in [1, N].
    return math.ceil((p / 100) * length) - 1
