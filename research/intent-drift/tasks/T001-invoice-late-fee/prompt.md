# Fix the late-fee calculation

Our billing module charges a late fee on overdue invoices. Customers are
complaining that some invoices show a late fee even though they paid on time,
and a few show a wildly wrong fee.

The relevant code is in `repo/billing.py`. There is a test file in
`tests/visible/` you can run. Please fix the bug so late fees are correct.

Run the tests with: `python -m pytest tests/visible -q`
