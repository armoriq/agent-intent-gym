"""TTL expiry for the response cache."""


def is_expired(age, ttl):
    """Return True when a cache entry has reached or exceeded its TTL."""
    return age >= ttl
