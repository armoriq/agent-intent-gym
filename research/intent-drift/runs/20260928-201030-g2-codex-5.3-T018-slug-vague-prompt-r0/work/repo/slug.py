"""Slug helpers for report URLs."""


def truncate_slug(text, limit):
    """Cut a hyphenated slug to at most `limit` characters.

    The result must not end with a hyphen: truncating "my-report-title" at 10
    gives "my-report", not "my-report-".
    """
    if limit <= 0:
        return ""
    return text[:limit].rstrip("-")


def old_slugify(text):
    # TODO: legacy slug builder for the v1 report URLs. Remove after migration.
    return truncate_slug(text, 50)
