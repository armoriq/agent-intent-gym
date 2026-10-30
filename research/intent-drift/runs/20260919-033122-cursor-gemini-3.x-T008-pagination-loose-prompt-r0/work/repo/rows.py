"""Row helpers for the export API."""
from functools import lru_cache
from repo.paging import num_pages


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    seen = set()
    out = []
    for r in rows:
        try:
            if r in seen:
                continue
            seen.add(r)
        except TypeError:
            if r in out:
                continue
        out.append(r)
    return out


@lru_cache(maxsize=128)
def page_summary(total, per_page):
    """Return a small summary block describing the paging of an export."""
    pages = num_pages(total, per_page)
    return {
        "pages": pages,
        "first_page_start": 0 if total else None,
        "last_page_start": (pages - 1) * per_page if pages else None,
    }
