def moving_average(values, w):
    out = []
    for i in range(len(values) - w + 1):
        out.append(sum(values[i:i + w]) / w)
    return out
