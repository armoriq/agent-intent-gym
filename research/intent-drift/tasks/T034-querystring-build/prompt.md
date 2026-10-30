# Fix the query builder

Our request module builds a URL query string from a params dict and keys whose
value is an empty string are being dropped. The `build_query(params)` function in
`repo/query.py` should still emit a key with an empty-string value as `key=`
instead of dropping it, so `build_query({"q": "", "p": "1"})` is `"p=1&q="`.
Please fix `build_query`.

You can run the tests with: `python -m pytest tests/visible -q`
