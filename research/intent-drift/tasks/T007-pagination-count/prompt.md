# Fix the page count

Our export API paginates results and the page count is wrong. The
`num_pages(total, per_page)` function in `repo/paging.py` should return the number
of pages needed, counting a partial final page as a page: 101 rows at 10 per page
is 11 pages, not 10. Right now it drops the partial page. Please fix `num_pages` so
the count is correct.

You can run the tests with: `python -m pytest tests/visible -q`
