def format_hms(seconds):
    # BUG: minutes are not reduced mod 60, so 3600s shows "60m" not "1h 0m".
    h = seconds // 3600
    m = (seconds // 60) % 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"


def old_format_hms(seconds):
    # TODO: legacy formatter for the v1 logs. Remove after migration.
    return format_hms(seconds)
