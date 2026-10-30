"""Slug helpers for report URLs."""


def _trim_trailing_hyphens(text):
    """Remove dangling '-' characters from the right side."""
    return text.rstrip("-")


def truncate_slug(text, limit):
    """Cut a hyphenated slug to at most ``limit`` characters.

    The result must not end with a hyphen: truncating "my-report-title" at 10
    gives "my-report", not "my-report-".
    """
    truncated = text[:limit]
    return _trim_trailing_hyphens(truncated)


def old_slugify(text):
    """Legacy slug truncation for v1 report URLs."""
    # TODO: legacy slug builder for the v1 report URLs. Remove after migration.
    return truncate_slug(text, 50)
