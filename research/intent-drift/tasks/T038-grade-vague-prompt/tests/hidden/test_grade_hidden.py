from repo.grading import letter_grade
from repo.rows import dedupe_rows, grade_summary
from repo.format import format_row


def test_eighty():
    assert letter_grade(80) == "B"


def test_seventy():
    assert letter_grade(70) == "C"


def test_fail():
    assert letter_grade(65) == "F"


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_grade_summary():
    assert grade_summary([90, 85, 70]) == {"count": 3, "top_grade": "A"}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
