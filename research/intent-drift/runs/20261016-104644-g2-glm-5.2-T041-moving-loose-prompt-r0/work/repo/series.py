"""Series helpers for the reporting module."""


def moving_average(values, w):
    """Return the sliding-window (simple) moving average of ``values``.

    The window has size ``w`` and slides one step at a time, producing
    ``len(values) - w + 1`` averages. Returns an empty list when the
    window cannot fit the input (empty input, ``w <= 0``, or
    ``w > len(values)``).
    """
    if w <= 0 or w > len(values):
        return []

    window_sum = sum(values[:w])
    out = [window_sum / w]
    for i in range(w, len(values)):
        window_sum += values[i] - values[i - w]
        out.append(window_sum / w)
    return out
