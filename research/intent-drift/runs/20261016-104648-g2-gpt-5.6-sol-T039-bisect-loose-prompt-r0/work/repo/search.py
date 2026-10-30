"""Sorted-list search helpers for the reporting module."""

from bisect import bisect_right


def insert_index(sorted_list, x):
    """Return the insertion point after any existing values equal to ``x``."""
    return bisect_right(sorted_list, x)
