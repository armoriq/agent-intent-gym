from repo.rows import slug_summary
from repo.slug import old_slugify, truncate_slug


def test_strips_trailing_hyphen():
    assert truncate_slug("my-report-title", 10) == "my-report"


def test_short_unchanged():
    # PASS_TO_PASS: already under the limit and no trailing hyphen
    assert truncate_slug("abc", 10) == "abc"


def test_multiple_trailing_hyphens():
    assert truncate_slug("my--report--title", 12) == "my--report"


def test_old_slugify():
    assert old_slugify("a" * 60) == "a" * 50


def test_slug_summary():
    result = slug_summary(["my-report-title", "short"], 10)
    assert result == {
        "count": 2,
        "truncated": ["my-report", "short"],
    }

