"""Helpers for simple numeric series operations."""


def _validate_window(w):
    """Ensure moving-average windows are positive integers."""
    if w <= 0:
        raise ValueError("window size must be greater than zero")


def moving_average(values, w):
    """Return all size-``w`` moving averages for ``values``."""
    _validate_window(w)

    if len(values) < w:
        return []

    window_sum = sum(values[:w])
    out = [window_sum / w]

    for right in range(w, len(values)):
        window_sum += values[right] - values[right - w]
        out.append(window_sum / w)

    return out


def old_moving_average(values, w):
    # Backward-compatible alias for old call sites.
    return moving_average(values, w)
