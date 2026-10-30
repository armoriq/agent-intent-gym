"""Series helpers for the reporting module."""


def moving_average(values, w):
    """Return the moving average of `values` over a window of size `w`.

    The result has one entry per full window, so it is empty when
    `w` is larger than the number of values.
    """
    if w <= 0:
        raise ValueError("window size must be positive")
    out = []
    for i in range(len(values) - w + 1):
        out.append(sum(values[i:i + w]) / w)
    return out
