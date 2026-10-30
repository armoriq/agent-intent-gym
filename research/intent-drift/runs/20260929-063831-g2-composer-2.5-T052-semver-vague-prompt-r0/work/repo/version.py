"""Version comparison for the updater module."""


def compare_versions(a, b):
    parts_a = [int(x) for x in a.split(".")]
    parts_b = [int(x) for x in b.split(".")]
    length = max(len(parts_a), len(parts_b))
    parts_a.extend([0] * (length - len(parts_a)))
    parts_b.extend([0] * (length - len(parts_b)))
    for pa, pb in zip(parts_a, parts_b):
        if pa < pb:
            return -1
        if pa > pb:
            return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
