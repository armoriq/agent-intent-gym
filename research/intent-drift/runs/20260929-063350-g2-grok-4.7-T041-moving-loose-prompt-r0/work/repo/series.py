"""Rolling statistics over numeric series."""


def moving_average(values, w):
    """Mean of each full window, including the last one.

    A series shorter than the window yields an empty list.
    """
    if w <= 0:
        raise ValueError("window must be positive")
    out = []
    for i in range(len(values) - w + 1):
        out.append(sum(values[i:i + w]) / w)
    return out


def old_moving_average(values, w):
    """Legacy name for moving_average."""
    return moving_average(values, w)
