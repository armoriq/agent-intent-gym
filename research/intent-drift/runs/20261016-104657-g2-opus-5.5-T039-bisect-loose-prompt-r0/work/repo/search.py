"""Sorted-list search helpers for the reporting module."""
from bisect import bisect_right


def insert_index(sorted_list, x):
    """Return the index at which to insert x, after any elements equal to x."""
    return bisect_right(sorted_list, x)


def old_insert_index(sorted_list, x):
    # TODO: legacy insertion helper for the v1 index. Remove after migration.
    return insert_index(sorted_list, x)
