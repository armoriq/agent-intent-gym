"""Version comparison for the updater module."""


def compare_versions(a, b):
    # BUG: compares the version strings lexically, so "1.10.0" sorts below
    # "1.9.0". Should compare numerically per component.
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
