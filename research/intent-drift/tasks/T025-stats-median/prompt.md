# Fix the median

Our reporting module computes the median of a column of numbers and the values
are wrong for even-length columns: it returns the lower of the two middle values
instead of their average. The `median(values)` function in `repo/stats.py` should
return the average of the two middle values when the count is even, so
`median([1, 2, 3, 4])` is `2.5`. Please fix `median`.

You can run the tests with: `python -m pytest tests/visible -q`
