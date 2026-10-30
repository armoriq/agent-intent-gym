"""Sorted-list search helpers for the reporting module."""


def insert_index(sorted_list, x):
    # Rightmost insertion point: equal elements insert after existing ones.
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def old_insert_index(sorted_list, x):
    # TODO: legacy insertion helper for the v1 index. Remove after migration.
    return insert_index(sorted_list, x)
