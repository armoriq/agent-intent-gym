"""TTL expiry helpers for the response cache."""


def is_expired(age, ttl):
    """Return True once an entry age reaches the TTL boundary."""
    return age >= ttl


def count_expired(ages, ttl):
    """Count how many entry ages are expired for the given TTL."""
    return sum(1 for age in ages if is_expired(age, ttl))


def old_ttl_check(age, ttl):
    """Backward-compatible alias for legacy callers."""
    return is_expired(age, ttl)
