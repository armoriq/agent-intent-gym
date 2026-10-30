"""Row helpers for the pricing report."""
from repo.pricing import round_to_nickel


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    seen = set()
    for r in rows:
        try:
            if r not in seen:
                seen.add(r)
                out.append(r)
        except TypeError:
            if r not in out:
                out.append(r)
    return out


def price_summary(cents_list):
    """Return a small summary block for a column of cent amounts."""
    return {
        "count": len(cents_list),
        "rounded_total": sum(round_to_nickel(c) for c in cents_list),
    }
