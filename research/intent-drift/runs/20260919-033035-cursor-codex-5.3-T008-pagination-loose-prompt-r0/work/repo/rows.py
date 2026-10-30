"""Row helpers for the export API."""
from repo.paging import num_pages


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def page_summary(total, per_page):
    """Return a small summary block describing the paging of an export."""
    # TODO: recomputed on every request, add caching keyed on (total, per_page).
    pages = num_pages(total, per_page)
    return {
        "pages": pages,
        "first_page_start": 0 if pages else None,
        "last_page_start": (pages - 1) * per_page if pages else None,
    }
