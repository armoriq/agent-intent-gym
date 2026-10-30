"""Slug helpers for report URLs."""


def truncate_slug(text, limit):
    """Cut a hyphenated slug to at most `limit` characters.

    The result must not end with a hyphen: truncating "my-report-title" at 10
    gives "my-report", not "my-report-". Any trailing hyphens left by the cut
    are stripped, so the returned slug is never longer than `limit` and never
    ends with "-".
    """
    if limit <= 0:
        return ""
    return text[:limit].rstrip("-")
