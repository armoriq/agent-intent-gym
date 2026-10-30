"""Row helpers for the pricing report."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from repo.pricing import round_to_nickel


def dedupe_rows(rows: Iterable[Any]) -> list[Any]:
    """Drop duplicate rows while preserving first-seen order."""
    out: list[Any] = []
    seen_hashable: set[Any] = set()

    for row in rows:
        try:
            if row in seen_hashable:
                continue
            seen_hashable.add(row)
            out.append(row)
        except TypeError:
            if row not in out:
                out.append(row)

    return out


def price_summary(cents_list: Iterable[int]) -> dict[str, int]:
    """Return count and nickel-rounded total for a column of cent amounts."""
    count = 0
    rounded_total = 0
    for cents in cents_list:
        count += 1
        rounded_total += round_to_nickel(cents)
    return {"count": count, "rounded_total": rounded_total}
