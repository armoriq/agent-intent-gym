"""Sorted-list search helpers for the reporting module."""


def insert_index(sorted_list, x):
    """Index at which to insert x so it stays sorted after any equal values."""
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo
