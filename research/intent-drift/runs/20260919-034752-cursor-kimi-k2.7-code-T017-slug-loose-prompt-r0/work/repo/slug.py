"""Slug helpers for report URLs."""


def truncate_slug(text, limit):
    """Cut a hyphenated slug to at most `limit` characters.

    The result must not end with a hyphen: truncating "my-report-title" at 10
    gives "my-report", not "my-report-".
    """
    return text[:limit].rstrip("-")


def old_slugify(text):
    """Legacy slug builder for v1 report URLs."""
    return truncate_slug(text, 50)
