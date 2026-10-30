"""Nickel rounding for the pricing report."""

_NICKEL = 5


def round_to_nickel(cents):
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20. Ties (e.g. a value
    exactly halfway between two nickels) round up.
    """
    return ((cents + _NICKEL // 2) // _NICKEL) * _NICKEL
