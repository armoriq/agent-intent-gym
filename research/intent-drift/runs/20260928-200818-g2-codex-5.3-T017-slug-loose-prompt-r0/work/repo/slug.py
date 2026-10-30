"""Slug helpers for report URLs."""


LEGACY_SLUG_LIMIT = 50


def _trim_trailing_hyphens(text):
    """Drop trailing hyphens from a slug fragment."""
    return text.rstrip("-")


def truncate_slug(text, limit):
    """Cut a slug to at most `limit` characters without dangling hyphens.

    The result must not end with a hyphen: truncating "my-report-title" at 10
    gives "my-report", not "my-report-".
    """
    if limit <= 0:
        return ""

    if len(text) <= limit:
        return _trim_trailing_hyphens(text)

    return _trim_trailing_hyphens(text[:limit])


def old_slugify(text):
    """Legacy slug builder for the v1 report URLs."""
    return truncate_slug(text, LEGACY_SLUG_LIMIT)
