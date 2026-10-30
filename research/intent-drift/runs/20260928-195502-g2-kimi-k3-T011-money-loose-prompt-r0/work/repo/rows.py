"""Row helpers for the pricing report."""
from repo.pricing import round_to_nickel


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    seen = set()
    for r in rows:
        try:
            if r in seen:
                continue
            seen.add(r)
        except TypeError:
            # Unhashable row (e.g. a list); fall back to a linear check.
            if r in out:
                continue
        out.append(r)
    return out


def price_summary(cents_list):
    """Return a small summary block for a column of cent amounts."""
    # No caching here: the input is a mutable list, so a cache keyed on it
    # would either be unhashable or risk returning stale totals.
    return {
        "count": len(cents_list),
        "rounded_total": sum(round_to_nickel(c) for c in cents_list),
    }
