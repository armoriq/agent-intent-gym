"""Sorted-list search helpers for the reporting module."""


def _right_insertion_index(sorted_list, x):
    """Return the index that inserts ``x`` after existing equal values."""
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if x < sorted_list[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


def insert_index(sorted_list, x):
    """Return the insertion index for ``x`` in ``sorted_list`` (right-biased)."""
    return _right_insertion_index(sorted_list, x)


def old_insert_index(sorted_list, x):
    """Legacy alias kept for the v1 index migration."""
    return _right_insertion_index(sorted_list, x)
