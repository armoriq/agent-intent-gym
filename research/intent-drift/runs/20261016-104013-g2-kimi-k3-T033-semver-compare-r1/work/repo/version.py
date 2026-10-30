"""Version comparison for the updater module."""


def compare_versions(a, b):
    parts_a = [int(p) for p in a.split(".")]
    parts_b = [int(p) for p in b.split(".")]
    length = max(len(parts_a), len(parts_b))
    parts_a += [0] * (length - len(parts_a))
    parts_b += [0] * (length - len(parts_b))
    for x, y in zip(parts_a, parts_b):
        if x < y:
            return -1
        if x > y:
            return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
