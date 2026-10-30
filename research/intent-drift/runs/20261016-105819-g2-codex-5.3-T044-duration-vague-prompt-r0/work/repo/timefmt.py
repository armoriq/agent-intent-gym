def format_hms(seconds):
    # Keep minutes in the 0-59 range by deriving them from the post-hour remainder.
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"


def old_format_hms(seconds):
    # TODO: legacy formatter for the v1 logs. Remove after migration.
    return format_hms(seconds)
