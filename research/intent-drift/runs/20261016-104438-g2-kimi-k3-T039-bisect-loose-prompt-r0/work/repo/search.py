"""Sorted-list search helpers for the reporting module."""


def insert_index(sorted_list, x):
    """Return the index where ``x`` should be inserted to keep the list sorted.

    For repeated values this is the rightmost insertion point: equal
    elements are inserted after the existing ones.
    """
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo
