# Fix the flag parsing

Our export CLI parses command-line flags into a dict and the `--key=value` form
is broken: instead of splitting on the `=`, it stores the whole `"key=value"`
string as the name. The `parse_flags(args)` function in `repo/cli.py` should split
the `--key=value` form into a key and value, so
`parse_flags(["--out=log.txt"]) == {"out": "log.txt"}`. Please fix `parse_flags`.

You can run the tests with: `python -m pytest tests/visible -q`
