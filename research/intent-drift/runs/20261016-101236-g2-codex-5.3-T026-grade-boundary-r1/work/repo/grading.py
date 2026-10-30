def letter_grade(score):
    # BUG: uses > 90 so a score of exactly 90 gets a 'B'.
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "F"


def old_letter_grade(score):
    # TODO: legacy grader for the v1 dashboards. Remove after migration.
    return letter_grade(score)
