"""Grading helpers for scoring and reports."""


def letter_grade(score):
    """Return the letter grade for a numeric score."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "F"


def old_letter_grade(score):
    """Legacy grader for v1 dashboards."""
    return letter_grade(score)
