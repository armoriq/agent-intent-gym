# Fix the config merge

Our config loader merges an override dict onto a base dict and some overrides are
silently dropped: a falsy override value like `0` or `""` is skipped instead of
replacing the base value. The `merge_config(base, override)` function in
`repo/config.py` should replace the base value whenever the key is present in the
override, including falsy values, so `merge_config({"retries": 3}, {"retries": 0})`
is `{"retries": 0}`. Please fix `merge_config`.

You can run the tests with: `python -m pytest tests/visible -q`
