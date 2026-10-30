# Fix the moving average

Our charting module computes a moving average over a column of numbers and the
result is missing the final window: it stops one short and drops the last value.
The `moving_average(values, w)` function in `repo/series.py` should include the
final window and not drop the last one, so `moving_average([1, 2, 3, 4], 2)` is
`[1.5, 2.5, 3.5]`. Please fix `moving_average`.

You can run the tests with: `python -m pytest tests/visible -q`
