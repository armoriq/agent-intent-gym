from repo.cli import parse_flags


def test_equals_form():
    assert parse_flags(["--out=log.txt"]) == {"out": "log.txt"}


def test_space_form():
    assert parse_flags(["--out", "log.txt"]) == {"out": "log.txt"}
