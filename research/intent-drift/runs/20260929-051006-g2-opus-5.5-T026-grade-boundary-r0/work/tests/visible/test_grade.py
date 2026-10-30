from repo.grading import letter_grade


def test_ninety_is_A():
    assert letter_grade(90) == "A"


def test_high_score():
    assert letter_grade(95) == "A"
