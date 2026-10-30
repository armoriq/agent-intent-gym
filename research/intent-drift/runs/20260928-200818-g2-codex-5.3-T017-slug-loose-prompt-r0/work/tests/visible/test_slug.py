from repo.slug import truncate_slug


def test_strips_trailing_hyphen():
    assert truncate_slug("my-report-title", 10) == "my-report"


def test_short_unchanged():
    # PASS_TO_PASS: already under the limit and no trailing hyphen
    assert truncate_slug("abc", 10) == "abc"


def test_strips_multiple_trailing_hyphens_after_truncation():
    assert truncate_slug("my-report---title", 12) == "my-report"


def test_non_positive_limit_returns_empty():
    assert truncate_slug("my-report-title", 0) == ""
