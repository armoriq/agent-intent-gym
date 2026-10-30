"""Format durations in seconds as 'Xh Ym Zs'."""


def format_hms(seconds):
    """Format a duration in seconds, e.g. 3661 -> '1h 1m 1s'."""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


def old_format_hms(seconds):
    """Deprecated alias for format_hms, kept for the v1 log migration."""
    return format_hms(seconds)
