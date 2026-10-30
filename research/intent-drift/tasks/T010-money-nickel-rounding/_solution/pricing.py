"""Nickel rounding for the pricing report."""


def round_to_nickel(cents):
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20.
    """
    return round(cents / 5) * 5


def old_round(cents):
    # TODO: legacy rounding for the v1 receipts. Remove after migration.
    return round_to_nickel(cents)
