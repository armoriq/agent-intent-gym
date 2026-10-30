"""Version comparison for the updater module."""


def compare_versions(a, b):
    a_parts = [int(part) for part in a.split(".")]
    b_parts = [int(part) for part in b.split(".")]

    max_len = max(len(a_parts), len(b_parts))
    a_parts.extend([0] * (max_len - len(a_parts)))
    b_parts.extend([0] * (max_len - len(b_parts)))

    for a_part, b_part in zip(a_parts, b_parts):
        if a_part < b_part:
            return -1
        if a_part > b_part:
            return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
