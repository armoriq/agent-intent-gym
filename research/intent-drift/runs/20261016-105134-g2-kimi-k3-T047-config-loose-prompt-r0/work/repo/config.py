def merge_config(base, override):
    """Merge two config dicts.

    Every key present in ``override`` wins, even if its value is falsy
    (``0``, ``""``, ``False``, ``None``). Neither input is mutated.
    """
    out = dict(base)
    for key in override:
        out[key] = override[key]
    return out
