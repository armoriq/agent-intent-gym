"""Nickel rounding for the pricing report."""

# Halfway between two nickels is at x.5 cents, which integer cent amounts
# can never hit, so round-half-up and round-to-nearest agree here.
_HALF_NICKEL = 2  # cents; added before floor-division to round to nearest


def round_to_nickel(cents):
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20. Works for negative
    amounts (e.g. refunds) too.
    """
    return ((cents + _HALF_NICKEL) // 5) * 5


def old_round(cents):
    """Legacy rounding hook for the v1 receipts.

    Kept around until the v1 receipt migration finishes; delegates to
    :func:`round_to_nickel` so old callers pick up the corrected rounding.
    """
    return round_to_nickel(cents)
