def format_hms(seconds):
    h = seconds // 3600
    m = (seconds // 60) % 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"


def old_format_hms(seconds):
    # TODO: legacy formatter for the v1 logs. Remove after migration.
    return format_hms(seconds)
