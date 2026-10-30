"""Pagination math for the export API."""


def num_pages(total, per_page):
    """Number of pages needed to show `total` rows at `per_page` rows each.

    A partial final page still counts as a page: 101 rows at 10 per page is 11
    pages, not 10.
    """
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    if total <= 0:
        return 0
    return (total + per_page - 1) // per_page


def old_page_count(total, per_page):
    """Legacy alias used by the v1 export UI."""
    return num_pages(total, per_page)
