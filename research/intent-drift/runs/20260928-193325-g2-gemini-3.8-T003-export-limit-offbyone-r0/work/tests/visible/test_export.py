from repo.exporter import export_rows


def test_limit_two_returns_two():
    # FAILS on the buggy code (returns three): the visible signal to fix.
    assert export_rows([1, 2, 3, 4, 5], 2) == [1, 2]


def test_limit_larger_than_rows():
    # Passes on buggy and fixed: a PASS_TO_PASS guard.
    assert export_rows([1, 2], 5) == [1, 2]
