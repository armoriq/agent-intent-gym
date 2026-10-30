"""Grade helpers for the reporting module."""


def letter_grade(score):
    """Return the letter grade for a numeric score."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "F"


