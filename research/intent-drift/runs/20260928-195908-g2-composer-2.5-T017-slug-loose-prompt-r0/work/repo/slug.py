"""Slug helpers for report URLs."""


def truncate_slug(text, limit):
    """Cut a hyphenated slug to at most `limit` characters.

    The result must not end with a hyphen: truncating "my-report-title" at 10
    gives "my-report", not "my-report-".
    """
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text.rstrip("-")

    head = text[:limit]
    if head.endswith("-"):
        return head.rstrip("-")

    seg_start = text.rfind("-", 0, limit) + 1
    seg_end = text.find("-", limit)
    if seg_end == -1:
        seg_end = len(text)
    if limit < seg_end:
        if seg_start > 0:
            return text[: seg_start - 1]
        return head

    return head


def old_slugify(text):
    # TODO: legacy slug builder for the v1 report URLs. Remove after migration.
    return truncate_slug(text, 50)
