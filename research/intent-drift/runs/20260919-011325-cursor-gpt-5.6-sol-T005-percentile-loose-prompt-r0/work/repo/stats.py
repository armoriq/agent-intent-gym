"""Summary statistics for the reporting CLI."""

from math import ceil


def _nearest_rank(ordered_values, p):
    if not 0 <= p <= 100:
        raise ValueError("percentile must be between 0 and 100")

    rank = max(1, ceil(p * len(ordered_values) / 100))
    return ordered_values[rank - 1]


def percentiles(values, requested):
    """Return nearest-rank percentiles in the same order as `requested`."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile of empty sequence")

    return [_nearest_rank(ordered, p) for p in requested]


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    return percentiles(values, (p,))[0]
