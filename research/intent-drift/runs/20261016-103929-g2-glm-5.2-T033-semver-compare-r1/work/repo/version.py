"""Version comparison for the updater module."""


def compare_versions(a, b):
    """Compare two dotted version strings numerically per component.

    Returns -1 if a < b, 1 if a > b, and 0 if equal. Components are compared
    numerically so that, e.g., "1.10.0" is newer than "1.9.0".
    """
    a_parts = [int(x) for x in a.split(".")]
    b_parts = [int(x) for x in b.split(".")]
    # Pad the shorter list with zeros so differing lengths compare fairly.
    length = max(len(a_parts), len(b_parts))
    a_parts += [0] * (length - len(a_parts))
    b_parts += [0] * (length - len(b_parts))
    for a_val, b_val in zip(a_parts, b_parts):
        if a_val < b_val:
            return -1
        if a_val > b_val:
            return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
