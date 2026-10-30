"""Nickel rounding for the pricing report."""

NICKEL_CENTS = 5


def round_to_nickel(cents: int) -> int:
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20.
    """
    # Adding half the interval before floor division gives nearest rounding.
    # Since a nickel contains an odd number of cents, integer inputs cannot tie.
    return ((cents + NICKEL_CENTS // 2) // NICKEL_CENTS) * NICKEL_CENTS


def old_round(cents: int) -> int:
    """Round legacy v1 receipt amounts using the current pricing rule."""
    return round_to_nickel(cents)
