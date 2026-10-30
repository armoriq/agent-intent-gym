def format_hms(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def old_format_hms(seconds):
    return format_hms(seconds)
