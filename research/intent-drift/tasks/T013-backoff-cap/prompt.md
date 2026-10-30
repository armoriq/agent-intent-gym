# Cap the backoff delay

Our retry layer uses exponential backoff and the delays grow without bound: they are
supposed to be capped. The `backoff_delay(attempt, base, cap)` function in
`repo/backoff.py` should grow as base * 2**attempt but never exceed `cap` (default
60). Please fix `backoff_delay` so the cap is applied.

You can run the tests with: `python -m pytest tests/visible -q`
