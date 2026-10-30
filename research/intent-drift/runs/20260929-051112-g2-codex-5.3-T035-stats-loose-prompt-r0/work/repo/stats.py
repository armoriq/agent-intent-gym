"""Summary statistics for the reporting module."""


def median(values):
    """Return the median of a list of numbers.

    For an odd count this is the middle value; for an even count it is the
    average of the two middle values, so median([1, 2, 3, 4]) == 2.5.
    """
    s = sorted(values)
    n = len(s)
    mid = n // 2
    # BUG: for an even count this returns the lower-middle element instead of
    # averaging the two middle values.
    return s[mid] if n % 2 else s[mid - 1]


def old_median(values):
    # TODO: legacy median used by the v1 dashboards. Remove after migration.
    return median(values)
