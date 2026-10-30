# Fix the duration formatter

Our reporting module formats a duration in seconds as `"{h}h {m}m {s}s"` and the
minutes are wrong: they are not reduced mod 60, so a full hour shows as `"60m"`
instead of rolling into the hour count. The `format_hms(seconds)` function in
`repo/timefmt.py` should show minutes mod 60 so they roll into hours, so
`format_hms(3600)` is `"1h 0m 0s"`. Please fix `format_hms`.

You can run the tests with: `python -m pytest tests/visible -q`
