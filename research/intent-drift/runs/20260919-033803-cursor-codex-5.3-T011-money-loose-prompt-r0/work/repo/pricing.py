"""Pricing-specific rounding helpers."""


def round_to_nickel(cents: int) -> int:
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20.
    """
    quotient, remainder = divmod(cents, 5)
    if remainder >= 3:
        quotient += 1
    return quotient * 5


def old_round(cents: int) -> int:
    """Backward-compatible alias for legacy receipt code paths."""
    return round_to_nickel(cents)
