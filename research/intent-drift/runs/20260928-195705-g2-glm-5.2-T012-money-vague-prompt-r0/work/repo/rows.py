"""Row helpers for the pricing report."""
from repo.pricing import round_to_nickel


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def price_summary(cents_list):
    """Return a small summary block for a column of cent amounts."""
    # TODO: recomputed on every call, add caching keyed on the input.
    return {
        "count": len(cents_list),
        "rounded_total": sum(round_to_nickel(c) for c in cents_list),
    }
