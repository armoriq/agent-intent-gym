"""Helpers for working with numeric series."""


def moving_average(values, w):
    """Return the arithmetic mean of each complete window in ``values``."""
    if not isinstance(w, int) or isinstance(w, bool):
        raise TypeError("window size must be an integer")
    if w <= 0:
        raise ValueError("window size must be positive")

    return [
        sum(values[start:start + w]) / w
        for start in range(len(values) - w + 1)
    ]


def old_moving_average(values, w):
    """Compatibility wrapper for the v1 chart API."""
    return moving_average(values, w)
