"""Row helpers for the pricing report."""
from repo.pricing import round_to_nickel


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order.

    Rows may be unhashable (e.g. lists), so we keep the linear membership
    check; correctness over cleverness for the export sizes we see today.
    """
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def price_summary(cents_list):
    """Return a small summary block for a column of cent amounts."""
    return {
        "count": len(cents_list),
        "rounded_total": sum(round_to_nickel(c) for c in cents_list),
    }
