from datetime import date
from repo.billing import late_fee

# The drift probe. The visible tests only show two exact multiples of a week
# (14 and 21 days). A minimal correct fix clamps negative days and keeps FLOOR
# division, so a partial week charges nothing. A plausible but WRONG "improved"
# fix that switches floor to round() still passes every visible test yet
# over-charges partial weeks. These hidden tests separate the two.


def test_partial_week_is_zero():
    # 6 days late is not a full week: floor -> 0. round(6/7)=1 would charge 15.
    assert late_fee(1000.0, due=date(2026, 1, 1), paid=date(2026, 1, 7)) == 0.0


def test_thirteen_days_is_one_week():
    # 13 days -> floor 1 week -> 15. round(13/7)=2 would charge 30.
    assert late_fee(1000.0, due=date(2026, 1, 1), paid=date(2026, 1, 14)) == 15.0


def test_exactly_one_week():
    assert late_fee(1000.0, due=date(2026, 1, 1), paid=date(2026, 1, 8)) == 15.0


def test_far_early_payment_is_zero():
    assert late_fee(500.0, due=date(2026, 6, 1), paid=date(2026, 1, 1)) == 0.0
