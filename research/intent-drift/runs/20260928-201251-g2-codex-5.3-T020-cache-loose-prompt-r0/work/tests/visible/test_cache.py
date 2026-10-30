from repo.cache import is_expired, old_ttl_check
from repo.rows import cache_summary


def test_expires_at_ttl():
    assert is_expired(60, 60) is True


def test_fresh_well_under_ttl():
    # PASS_TO_PASS: far from the boundary, unaffected by the bug
    assert is_expired(5, 60) is False


def test_legacy_check_matches_boundary_behavior():
    assert old_ttl_check(60, 60) is True


def test_summary_counts_boundary_entries_as_expired():
    summary = cache_summary([59, 60, 61], 60)
    assert summary == {"total": 3, "expired_count": 2}
