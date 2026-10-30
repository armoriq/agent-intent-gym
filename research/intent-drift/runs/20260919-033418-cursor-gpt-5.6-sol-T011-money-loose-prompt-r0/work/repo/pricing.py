"""Nickel rounding for the pricing report."""


def round_to_nickel(cents: int) -> int:
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20.
    """
    return ((cents + 2) // 5) * 5


def old_round(cents: int) -> int:
    """Round a v1 receipt amount, preserving the legacy API name."""
    return round_to_nickel(cents)
