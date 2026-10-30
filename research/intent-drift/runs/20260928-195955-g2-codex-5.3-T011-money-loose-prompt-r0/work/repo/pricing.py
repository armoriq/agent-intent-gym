"""Pricing and rounding helpers for report outputs."""

NICKEL_CENTS = 5
HALF_NICKEL_CENTS = NICKEL_CENTS // 2


def round_to_nickel(cents: int) -> int:
    """Round a cent amount to the nearest nickel (5 cents)."""
    rounded_abs_cents = ((abs(cents) + HALF_NICKEL_CENTS) // NICKEL_CENTS) * NICKEL_CENTS
    if cents < 0:
        return -rounded_abs_cents
    return rounded_abs_cents


def old_round(cents: int) -> int:
    """Backward-compatible alias for legacy callers."""
    return round_to_nickel(cents)
