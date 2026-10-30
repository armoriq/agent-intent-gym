"""Letter grades for numeric scores."""


def letter_grade(score):
    """Map a numeric score to a letter grade.

    Cutoffs are inclusive: 90 is an A, 80 is a B, and 70 is a C.
    Scores below 70 are an F.
    """
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "F"


def old_letter_grade(score):
    """Legacy alias for letter_grade, kept for v1 dashboards."""
    return letter_grade(score)
