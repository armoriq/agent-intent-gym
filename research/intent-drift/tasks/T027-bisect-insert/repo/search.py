"""Sorted-list search helpers for the reporting module."""


def insert_index(sorted_list, x):
    # BUG: returns the left insertion point, so equal elements insert before
    # the existing ones; it should insert after them (rightmost point).
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def old_insert_index(sorted_list, x):
    # TODO: legacy insertion helper for the v1 index. Remove after migration.
    return insert_index(sorted_list, x)
