"""Time formatting helpers."""


def format_hms(seconds):
    """Format elapsed seconds as '<hours>h <minutes>m <seconds>s'."""
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    return f"{h}h {m}m {s}s"


def old_format_hms(seconds):
    """Legacy alias used by v1 logs during migration."""
    return format_hms(seconds)
