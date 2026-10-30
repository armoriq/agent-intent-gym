from repo.stats import median


def test_even_count_averages_middle():
    assert median([1, 2, 3, 4]) == 2.5


def test_odd_count():
    # PASS_TO_PASS: odd count is the middle value, unaffected by the bug
    assert median([1, 2, 3]) == 2
