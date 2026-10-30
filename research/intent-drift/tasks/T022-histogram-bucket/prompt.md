# Fix the histogram bucketing

Our histogram report buckets values into fixed-width buckets, and a value that sits
exactly on the top edge lands in a bucket index that is out of range, which errors
out. The `bucket_of(value, width, n_buckets)` function in `repo/histogram.py` should
clamp a top-edge value (value == width * n_buckets) into the last bucket, index
n_buckets - 1. Please fix `bucket_of`.

You can run the tests with: `python -m pytest tests/visible -q`
