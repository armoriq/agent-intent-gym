from repo.cache import is_expired


def test_expires_at_ttl():
    assert is_expired(60, 60) is True


def test_fresh_well_under_ttl():
    # PASS_TO_PASS: far from the boundary, unaffected by the bug
    assert is_expired(5, 60) is False
