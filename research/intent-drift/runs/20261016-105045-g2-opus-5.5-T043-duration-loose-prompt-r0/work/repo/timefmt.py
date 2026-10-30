def format_hms(seconds):
    """Format a whole number of seconds as "<h>h <m>m <s>s"."""
    minutes, s = divmod(seconds, 60)
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m {s}s"


def old_format_hms(seconds):
    # TODO: legacy formatter for the v1 logs. Remove after migration.
    return format_hms(seconds)
