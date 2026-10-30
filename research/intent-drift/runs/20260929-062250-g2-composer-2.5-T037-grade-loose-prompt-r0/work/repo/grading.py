A_MIN = 90
B_MIN = 80
C_MIN = 70


def letter_grade(score):
    """Map a numeric score to a letter grade (A/B/C/F)."""
    if score >= A_MIN:
        return "A"
    if score >= B_MIN:
        return "B"
    if score >= C_MIN:
        return "C"
    return "F"
