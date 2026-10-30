"""Version comparison for the updater module."""


def compare_versions(a, b):
    a_parts = [int(part) for part in a.split(".")]
    b_parts = [int(part) for part in b.split(".")]
    max_len = max(len(a_parts), len(b_parts))

    for i in range(max_len):
        a_part = a_parts[i] if i < len(a_parts) else 0
        b_part = b_parts[i] if i < len(b_parts) else 0

        if a_part < b_part:
            return -1
        if a_part > b_part:
            return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
