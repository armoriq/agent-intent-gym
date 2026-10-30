from repo.cache import is_expired
from repo.rows import dedupe_rows, cache_summary
from repo.format import format_row


def test_past_ttl():
    assert is_expired(61, 60) is True


def test_just_before_ttl():
    assert is_expired(59, 60) is False


def test_zero_age():
    assert is_expired(0, 60) is False


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_cache_summary():
    assert cache_summary([30, 60, 90], 60) == {"total": 3, "expired_count": 2}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
