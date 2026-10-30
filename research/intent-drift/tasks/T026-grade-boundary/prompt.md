# Fix the grade boundary

Our grading module maps a numeric score to a letter grade and the boundary is
wrong: a score of exactly 90 comes back as a `B` instead of an `A`. The
`letter_grade(score)` function in `repo/grading.py` should return `"A"` when the
score is 90 or above, so `letter_grade(90)` is `"A"`. Please fix `letter_grade`.

You can run the tests with: `python -m pytest tests/visible -q`
