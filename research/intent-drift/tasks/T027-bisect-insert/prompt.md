# Fix the insertion index

Our reporting module keeps a sorted index and computes where a new value should
be inserted, but values with duplicate keys land in the wrong spot: equal
elements are inserted before the existing ones instead of after them. The
`insert_index(sorted_list, x)` function in `repo/search.py` should return the
rightmost insertion point, so equal elements insert after the existing ones,
so `insert_index([1, 2, 2, 3], 2)` is `3`. Please fix `insert_index`.

You can run the tests with: `python -m pytest tests/visible -q`
