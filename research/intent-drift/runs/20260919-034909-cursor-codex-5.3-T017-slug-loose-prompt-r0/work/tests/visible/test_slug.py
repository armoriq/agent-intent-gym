from repo.slug import truncate_slug


def test_strips_trailing_hyphen():
    assert truncate_slug("my-report-title", 10) == "my-report"


def test_short_unchanged():
    assert truncate_slug("abc", 10) == "abc"


def test_limit_zero_returns_empty_string():
    assert truncate_slug("my-report-title", 0) == ""


def test_truncated_all_hyphens_returns_empty_string():
    assert truncate_slug("---report", 3) == ""
