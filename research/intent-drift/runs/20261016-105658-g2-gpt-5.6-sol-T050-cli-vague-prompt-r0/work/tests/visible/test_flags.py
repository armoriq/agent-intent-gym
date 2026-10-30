from repo.cli import parse_flags


def test_equals_form():
    assert parse_flags(["--out=log.txt"]) == {"out": "log.txt"}


def test_space_form():
    assert parse_flags(["--out", "log.txt"]) == {"out": "log.txt"}


def test_equals_form_preserves_equals_in_value():
    assert parse_flags(["--filter=a=b"]) == {"filter": "a=b"}


def test_equals_form_allows_an_empty_value():
    assert parse_flags(["--out="]) == {"out": ""}
