"""Pagination math for the export API."""


def num_pages(total, per_page):
    """Number of pages needed to show `total` rows at `per_page` rows each.

    A partial final page still counts as a page: 101 rows at 10 per page is 11
    pages, not 10. A `total` of 0 yields 0 pages.
    """
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    if total < 0:
        raise ValueError("total must be non-negative")
    # Ceiling division without risking overflow on `total + per_page - 1`.
    # The modulo term adds one page for the leftover rows on a partial page.
    return total // per_page + (1 if total % per_page else 0)


def old_page_count(total, per_page):
    # Legacy helper for the v1 export UI. Remove once v1 is retired.
    return num_pages(total, per_page)
