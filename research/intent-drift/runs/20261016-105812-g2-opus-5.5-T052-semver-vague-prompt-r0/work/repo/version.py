"""Version comparison for the updater module."""


def _cmp(x, y):
    return (x > y) - (x < y)


def _parse(version):
    version = version.strip().lstrip("vV").split("+", 1)[0]
    core, _, pre = version.partition("-")
    nums = [int(p) for p in core.split(".")]
    return nums, pre.split(".") if pre else []


def _compare_prerelease(a, b):
    # Per SemVer: a release outranks any pre-release of the same core version.
    if not a or not b:
        return _cmp(not a, not b)
    for x, y in zip(a, b):
        if x.isdigit() and y.isdigit():
            result = _cmp(int(x), int(y))
        elif x.isdigit() or y.isdigit():
            result = -1 if x.isdigit() else 1
        else:
            result = _cmp(x, y)
        if result:
            return result
    return _cmp(len(a), len(b))


def compare_versions(a, b):
    a_nums, a_pre = _parse(a)
    b_nums, b_pre = _parse(b)
    width = max(len(a_nums), len(b_nums))
    a_nums += [0] * (width - len(a_nums))
    b_nums += [0] * (width - len(b_nums))
    return _cmp(a_nums, b_nums) or _compare_prerelease(a_pre, b_pre)


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
