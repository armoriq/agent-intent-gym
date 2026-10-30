"""Sorted-list search helpers for the reporting module."""


def insert_index(sorted_list, x):
    """Return the rightmost index at which ``x`` can be inserted to keep ``sorted_list`` sorted.

    Equal elements are inserted *after* the existing ones, so the returned
    index is the count of elements strictly less than ``x`` plus the count of
    elements equal to ``x``. Runs in O(log n) time.
    """
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo
