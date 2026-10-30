"""Summary statistics for the reporting module."""


def median(values):
    """Return the median of a list of numbers.

    For an odd count this is the middle value; for an even count it is the
    average of the two middle values, so median([1, 2, 3, 4]) == 2.5.
    """
    if not values:
        raise ValueError("median of empty sequence")
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2
