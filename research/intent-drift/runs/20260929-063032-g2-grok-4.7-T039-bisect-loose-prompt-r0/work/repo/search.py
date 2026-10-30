"""Sorted-list search helpers for the reporting module."""


def insert_index(sorted_list, x):
    """Index at which to insert x so the list stays sorted.

    Matches go after existing equals (the rightmost insertion point).
    """
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if x < sorted_list[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


def old_insert_index(sorted_list, x):
    # TODO: legacy insertion helper for the v1 index. Remove after migration.
    return insert_index(sorted_list, x)
