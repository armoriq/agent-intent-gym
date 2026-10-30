"""Version comparison for the updater module."""


def _parse(version):
    """Split a dotted version string into numeric components.

    Raises ValueError if any component is not a non-negative integer.
    """
    parts = version.strip().split(".")
    components = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"invalid version component {part!r} in {version!r}")
        components.append(int(part))
    return components


def compare_versions(a, b):
    """Compare two dotted version strings numerically, component by component.

    Returns -1 if a < b, 0 if a == b, 1 if a > b. Missing trailing
    components are treated as zeros, so "1.2" equals "1.2.0".
    """
    parts_a = _parse(a)
    parts_b = _parse(b)

    width = max(len(parts_a), len(parts_b))
    parts_a.extend([0] * (width - len(parts_a)))
    parts_b.extend([0] * (width - len(parts_b)))

    if parts_a < parts_b:
        return -1
    if parts_a > parts_b:
        return 1
    return 0
