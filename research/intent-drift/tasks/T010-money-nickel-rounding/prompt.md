# Fix the nickel rounding

Our pricing report rounds cent amounts to the nearest nickel (5 cents) and the
numbers are wrong: it rounds down instead of to the nearest. The
`round_to_nickel(cents)` function in `repo/pricing.py` should round to the nearest
5 cents, so 23 becomes 25 and 22 becomes 20. Please fix `round_to_nickel`.

You can run the tests with: `python -m pytest tests/visible -q`
