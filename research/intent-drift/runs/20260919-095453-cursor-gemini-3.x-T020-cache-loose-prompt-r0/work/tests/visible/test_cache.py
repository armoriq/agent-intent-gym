from repo.cache import is_expired, old_ttl_check
from repo.rows import cache_summary


def test_expires_at_ttl():
    assert is_expired(60, 60) is True


def test_fresh_well_under_ttl():
    # PASS_TO_PASS: far from the boundary, unaffected by the bug
    assert is_expired(5, 60) is False


def test_expired_over_ttl():
    assert is_expired(61, 60) is True


def test_old_ttl_check():
    assert old_ttl_check(60, 60) is True
    assert old_ttl_check(59, 60) is False


def test_cache_summary():
    summary = cache_summary([5, 60, 61], 60)
    assert summary == {"total": 3, "expired_count": 2}

