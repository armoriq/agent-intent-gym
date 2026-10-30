"""Helpers for converting numeric scores to letter grades."""

# Keep grade bands in one place so updates are easy and less error-prone.
_GRADE_BANDS = (
    (90, "A"),
    (80, "B"),
    (70, "C"),
)


def letter_grade(score):
    """Return a letter grade for a numeric score."""
    for cutoff, grade in _GRADE_BANDS:
        if score >= cutoff:
            return grade
    return "F"


def old_letter_grade(score):
    """Legacy alias for the v1 dashboards."""
    return letter_grade(score)
