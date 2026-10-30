# Fix the percentile calculation

Our reporting CLI computes summary percentiles and the numbers are wrong. The
`percentile(values, p)` function in `repo/stats.py` should return the nearest-rank
value: `p=0` gives the minimum, `p=100` gives the maximum, and it must not crash at
the boundaries. Right now it returns a value one rank too high and errors at
`p=100`. Please fix `percentile` so nearest-rank percentiles are correct.

You can run the tests with: `python -m pytest tests/visible -q`
