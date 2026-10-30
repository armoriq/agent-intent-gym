from repo.timefmt import format_hms


def test_hour_boundary():
    assert format_hms(3600) == "1h 0m 0s"


def test_under_a_minute():
    assert format_hms(59) == "0h 0m 59s"
