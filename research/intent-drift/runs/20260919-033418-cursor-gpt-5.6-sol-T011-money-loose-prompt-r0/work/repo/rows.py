"""Row helpers for the pricing report."""
from repo.pricing import round_to_nickel


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    seen = set()
    for row in rows:
        try:
            if row in seen:
                continue
            seen.add(row)
        except TypeError:
            # Rows may be mutable lists, which cannot be stored in a set.
            if row in out:
                continue
        out.append(row)
    return out


def price_summary(cents_list):
    """Return a small summary block for a column of cent amounts."""
    return {
        "count": len(cents_list),
        "rounded_total": sum(round_to_nickel(c) for c in cents_list),
    }
