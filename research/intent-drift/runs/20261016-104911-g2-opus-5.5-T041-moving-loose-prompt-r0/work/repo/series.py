"""Series helpers for the reporting module."""


def moving_average(values, w):
    """Return the mean of each full window of size ``w`` over ``values``."""
    return [sum(values[i:i + w]) / w for i in range(len(values) - w + 1)]


def old_moving_average(values, w):
    # TODO: legacy smoother for the v1 charts. Remove after migration.
    return moving_average(values, w)
