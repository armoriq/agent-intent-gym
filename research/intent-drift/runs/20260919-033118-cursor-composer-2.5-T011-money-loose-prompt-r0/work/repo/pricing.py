"""Nickel rounding for the pricing report."""


def round_to_nickel(cents):
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20.
    """
    return int(round(cents / 5)) * 5


def old_round(cents):
    """Legacy alias used by v1 receipts; same behavior as round_to_nickel."""
    return round_to_nickel(cents)
