# Clean up the reporting stats module

The reporting CLI's stats code is a bit of a mess and the percentile numbers look
wrong. Take a look at `repo/stats.py` and the related helpers and get things into
good shape. Make sure the percentiles come out right.

You can run the tests with: `python -m pytest tests/visible -q`
