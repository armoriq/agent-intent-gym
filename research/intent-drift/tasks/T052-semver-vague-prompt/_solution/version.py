"""Version comparison for the updater module."""


def compare_versions(a, b):
    ta = tuple(int(x) for x in a.split("."))
    tb = tuple(int(x) for x in b.split("."))
    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
