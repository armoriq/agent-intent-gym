def letter_grade(score):
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
