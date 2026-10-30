"""Nickel rounding for the pricing report."""


def round_to_nickel(cents):
    """Round an integer cent amount to the nearest 5 cents.

    23 cents rounds to 25, 22 cents rounds to 20.
    """
    # Adding 2 before floor-dividing rounds half-up; with integer cents
    # there is no exact tie (2.5 cents), so this is unambiguous. The
    # floor division also keeps negative amounts rounding to nearest.
    return ((cents + 2) // 5) * 5


def old_round(cents):
    """Deprecated alias kept for v1 receipts until the migration completes."""
    return round_to_nickel(cents)
