from repo.cli import parse_flags


def test_equals_form():
    assert parse_flags(["--out=log.txt"]) == {"out": "log.txt"}


def test_space_form():
    assert parse_flags(["--out", "log.txt"]) == {"out": "log.txt"}


def test_boolean_flag():
    assert parse_flags(["--verbose"]) == {"verbose": True}


def test_equals_form_preserves_empty_value():
    assert parse_flags(["--out="]) == {"out": ""}


def test_equals_form_splits_only_once():
    assert parse_flags(["--filter=name=value"]) == {"filter": "name=value"}


def test_equals_form_does_not_consume_following_argument():
    assert parse_flags(["--out=log.txt", "--verbose"]) == {
        "out": "log.txt",
        "verbose": True,
    }
