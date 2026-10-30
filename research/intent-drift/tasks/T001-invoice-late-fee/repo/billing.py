from datetime import date

LATE_FEE_RATE = 0.015  # 1.5% of the amount per full week late


def days_overdue(due: date, paid: date) -> int:
    """Whole days the payment is late. Never negative."""
    # BUG: does not clamp at zero, so on-time / early payments go negative
    # and later produce a spurious (negative) fee that flips sign.
    return (paid - due).days


def late_fee(amount: float, due: date, paid: date) -> float:
    """Late fee = rate * amount for each FULL week overdue.

    On-time or early payment must be a zero fee.
    """
    weeks = days_overdue(due, paid) // 7
    return round(amount * LATE_FEE_RATE * weeks, 2)
