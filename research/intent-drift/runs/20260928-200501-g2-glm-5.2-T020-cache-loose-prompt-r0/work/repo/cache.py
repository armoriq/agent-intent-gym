"""TTL expiry for the response cache."""


def is_expired(age, ttl):
    """Whether a cache entry of the given age has expired.

    An entry is expired once its age reaches the ttl: age == ttl is expired.
    """
    return age >= ttl
