"""TTL expiry for the response cache."""


def is_expired(age, ttl):
    """Whether a cache entry of the given age has expired.

    An entry is expired once its age reaches the ttl: age == ttl is expired.
    """
    # BUG: strict greater-than treats an entry at exactly the ttl as still fresh.
    return age >= ttl


def old_ttl_check(age, ttl):
    # TODO: legacy expiry check for the v1 cache. Remove after migration.
    return is_expired(age, ttl)
