"""Summary statistics for the reporting CLI."""

from math import ceil
from numbers import Real


def _nearest_rank_index(length, p):
    """Return the 0-based nearest-rank index for percentile `p`."""
    if p == 0:
        return 0
    return ceil((p / 100) * length) - 1


def _validate_percentile(p):
    """Validate percentile input and normalize to float."""
    if not isinstance(p, Real):
        raise TypeError("percentile `p` must be a real number")
    p = float(p)
    if p < 0 or p > 100:
        raise ValueError("percentile `p` must be in [0, 100]")
    return p


def percentile_from_sorted(ordered_values, p):
    """Nearest-rank percentile of pre-sorted values for percentile `p`."""
    if not ordered_values:
        raise ValueError("percentile of empty sequence")

    p = _validate_percentile(p)
    idx = _nearest_rank_index(len(ordered_values), p)
    return ordered_values[idx]


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    ordered = sorted(values)
    return percentile_from_sorted(ordered, p)


def old_percentile(values, p):
    """Legacy alias for percentile()."""
    return percentile(values, p)
