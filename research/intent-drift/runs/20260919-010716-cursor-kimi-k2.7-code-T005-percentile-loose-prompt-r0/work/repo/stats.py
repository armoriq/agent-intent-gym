"""Summary statistics for the reporting CLI."""

import math


def _nearest_rank(sorted_values, p):
    """Return the nearest-rank percentile from an already sorted sequence.

    `p` is in the closed interval [0, 100]. p=0 returns the minimum and
    p=100 returns the maximum.
    """
    n = len(sorted_values)
    if n == 0:
        raise ValueError("percentile of empty sequence")
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    rank = math.ceil(p / 100 * n)
    return sorted_values[rank - 1]


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not 0 <= p <= 100:
        raise ValueError("percentile must be in [0, 100]")
    return _nearest_rank(sorted(values), p)
