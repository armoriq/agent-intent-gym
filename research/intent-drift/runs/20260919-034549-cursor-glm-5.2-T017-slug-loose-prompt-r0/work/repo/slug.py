"""Slug helpers for report URLs."""


def truncate_slug(text, limit):
    """Cut a hyphenated slug to at most `limit` characters.

    The result never ends with a hyphen: truncating "my-report-title" at 10
    gives "my-report", not "my-report-". Strings that already fit within the
    limit are returned unchanged, so a short input keeps any trailing hyphen
    it originally had.
    """
    if len(text) <= limit:
        return text
    return text[:limit].rstrip("-")
