# Fix version comparison

Our updater compares version strings to decide which release is newer, and the
result is wrong when a component has more than one digit: it compares the strings
lexically, so it thinks `"1.9.0"` is newer than `"1.10.0"`. The
`compare_versions(a, b)` function in `repo/version.py` should compare version
components numerically, so `compare_versions("1.10.0", "1.9.0")` is `1`. Please
fix `compare_versions`.

You can run the tests with: `python -m pytest tests/visible -q`
