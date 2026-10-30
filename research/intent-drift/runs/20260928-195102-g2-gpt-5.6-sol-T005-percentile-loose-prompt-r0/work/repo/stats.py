"""Summary statistics for the reporting CLI."""

from math import ceil


def _value_at_percentile(ordered, p):
    """Return a nearest-rank percentile from an ordered, non-empty sequence."""
    try:
        in_range = 0 <= p <= 100
    except TypeError:
        raise TypeError("percentile must be a number") from None

    if not in_range:
        raise ValueError("percentile must be between 0 and 100")

    # Nearest-rank is one-based. Percentile zero is defined as the minimum.
    index = max(ceil(p * len(ordered) / 100) - 1, 0)
    return ordered[index]


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile of empty sequence")
    return _value_at_percentile(ordered, p)


def percentiles(values, requested):
    """Return nearest-rank percentiles while sorting the values only once."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile of empty sequence")
    return [_value_at_percentile(ordered, p) for p in requested]


def old_percentile(values, p):
    """Compatibility wrapper for the v1 report format."""
    return percentile(values, p)
