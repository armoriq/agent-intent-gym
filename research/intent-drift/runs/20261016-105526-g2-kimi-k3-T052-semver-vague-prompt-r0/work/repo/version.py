"""Version comparison for the updater module."""


def _parse(version):
    parts = str(version).lstrip("v").split(".")
    return [int(p) for p in parts]


def compare_versions(a, b):
    pa, pb = _parse(a), _parse(b)
    # Pad the shorter version with zeros so 1.2 == 1.2.0.
    n = max(len(pa), len(pb))
    pa += [0] * (n - len(pa))
    pb += [0] * (n - len(pb))
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
