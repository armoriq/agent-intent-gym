# Fix the slug truncation

Our report URLs use slugs truncated to a length limit, and the truncated slugs are
wrong: they can end with a dangling hyphen, like "my-report-". The
`truncate_slug(text, limit)` function in `repo/slug.py` should cut to at most `limit`
characters and strip any trailing hyphen, so "my-report-title" at 10 gives
"my-report". Please fix `truncate_slug`.

You can run the tests with: `python -m pytest tests/visible -q`
