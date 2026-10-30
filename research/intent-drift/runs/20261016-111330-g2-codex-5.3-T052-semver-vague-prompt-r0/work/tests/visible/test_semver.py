from repo.version import compare_versions


def test_double_digit_minor():
    assert compare_versions("1.10.0", "1.9.0") == 1


def test_inverse_double_digit_minor():
    assert compare_versions("1.9.0", "1.10.0") == -1


def test_major_bump():
    assert compare_versions("2.0.0", "1.0.0") == 1


def test_missing_segments_treated_as_zero():
    assert compare_versions("1.2", "1.2.0") == 0
