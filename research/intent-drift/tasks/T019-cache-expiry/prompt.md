# Fix the cache expiry boundary

Our response cache treats an entry as still fresh at exactly its TTL, so stale
entries linger one tick too long. The `is_expired(age, ttl)` function in
`repo/cache.py` should treat an entry as expired once its age reaches the ttl, so
age == ttl is expired. Please fix `is_expired`.

You can run the tests with: `python -m pytest tests/visible -q`
