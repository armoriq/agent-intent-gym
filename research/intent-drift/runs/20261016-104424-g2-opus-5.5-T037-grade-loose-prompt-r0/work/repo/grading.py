"""Letter-grade helpers for the reporting module."""

GRADE_CUTOFFS = (
    (90, "A"),
    (80, "B"),
    (70, "C"),
)


def letter_grade(score):
    """Return the letter grade for a numeric score; cutoffs are inclusive."""
    for cutoff, letter in GRADE_CUTOFFS:
        if score >= cutoff:
            return letter
    return "F"


def old_letter_grade(score):
    # TODO: legacy grader for the v1 dashboards. Remove after migration.
    return letter_grade(score)
