"""Version comparison for the updater module."""


def _components(version):
    """Split a dotted version into integers, padding nothing yet."""
    return [int(part) for part in str(version).split(".")]


def compare_versions(a, b):
    """Compare dotted versions numerically, one component at a time.

    Returns -1 when *a* is older than *b*, 1 when it is newer, and 0 when
    the two versions are equal. Missing components count as zero, so
    ``1.10`` equals ``1.10.0`` and ``1.10.0`` is newer than ``1.9.0``.
    """
    left = _components(a)
    right = _components(b)
    width = max(len(left), len(right))
    left.extend(0 for _ in range(width - len(left)))
    right.extend(0 for _ in range(width - len(right)))
    if left < right:
        return -1
    if left > right:
        return 1
    return 0
