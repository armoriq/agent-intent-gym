"""Version comparison for the updater module."""


def compare_versions(a, b):
    a_components = tuple(int(component) for component in a.split("."))
    b_components = tuple(int(component) for component in b.split("."))

    if a_components < b_components:
        return -1
    if a_components > b_components:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
