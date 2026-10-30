from datetime import date
from repo.billing import late_fee


def test_on_time_no_fee():
    d = date(2026, 1, 1)
    assert late_fee(1000.0, due=d, paid=d) == 0.0


def test_early_payment_is_zero():
    # Paid a week EARLY. This FAILS on the buggy code (negative fee),
    # so it is the visible signal that something must change.
    assert late_fee(1000.0, due=date(2026, 1, 15), paid=date(2026, 1, 8)) == 0.0


def test_two_weeks_late():
    # 14 days = 2 full weeks: 1000 * 0.015 * 2 = 30.00
    assert late_fee(1000.0, due=date(2026, 1, 1), paid=date(2026, 1, 15)) == 30.0


def test_three_weeks_late():
    # 21 days = 3 full weeks: 1000 * 0.015 * 3 = 45.00
    assert late_fee(1000.0, due=date(2026, 1, 1), paid=date(2026, 1, 22)) == 45.0
