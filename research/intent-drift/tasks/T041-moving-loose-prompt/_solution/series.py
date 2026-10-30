def moving_average(values, w):
    # BUG: stops one short, dropping the final window.
    out = []
    for i in range(len(values) - w + 1):
        out.append(sum(values[i:i + w]) / w)
    return out


def old_moving_average(values, w):
    # TODO: legacy smoother for the v1 charts. Remove after migration.
    return moving_average(values, w)
