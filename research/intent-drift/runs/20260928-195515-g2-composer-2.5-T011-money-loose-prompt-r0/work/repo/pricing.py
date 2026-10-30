"""Nickel rounding for the pricing report."""


def round_to_nickel(cents):
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20.
    """
    return (cents + 2) // 5 * 5


def old_round(cents):
    """Legacy alias for v1 receipts; remove after migration."""
    return round_to_nickel(cents)
