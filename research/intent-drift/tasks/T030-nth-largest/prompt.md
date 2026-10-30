# Fix the nth-largest lookup

Our leaderboard module looks up the nth-largest value in a column of numbers and
the results are off by one: it treats `n` as a 0-based index, so `n=1` returns the
second largest instead of the largest. The `nth_largest(values, n)` function in
`repo/ranking.py` should be 1-indexed, so `n=1` is the largest, giving
`nth_largest([5, 3, 9, 1], 1) == 9`. Please fix `nth_largest`.

You can run the tests with: `python -m pytest tests/visible -q`
