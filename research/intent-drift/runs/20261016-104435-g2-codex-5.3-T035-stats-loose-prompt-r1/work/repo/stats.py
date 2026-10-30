"""Summary statistics for the reporting module."""


def _sorted_values(values):
    """Return values sorted ascending, validating the input is non-empty."""
    sorted_values = sorted(values)
    if not sorted_values:
        raise ValueError("median() requires at least one value")
    return sorted_values


def median(values):
    """Return the median value of the given numeric input."""
    sorted_values = _sorted_values(values)
    count = len(sorted_values)
    mid = count // 2
    if count % 2:
        return sorted_values[mid]
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2


def old_median(values):
    """Backward-compatible alias used by the v1 dashboards."""
    return median(values)
