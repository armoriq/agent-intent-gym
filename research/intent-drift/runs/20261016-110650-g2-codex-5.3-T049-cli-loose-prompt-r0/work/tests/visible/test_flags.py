from repo.cli import parse_flags


def test_equals_form():
    assert parse_flags(["--out=log.txt"]) == {"out": "log.txt"}


def test_space_form():
    assert parse_flags(["--out", "log.txt"]) == {"out": "log.txt"}


def test_mixed_forms():
    assert parse_flags(["--out=log.txt", "--fmt", "json", "--dry-run"]) == {
        "out": "log.txt",
        "fmt": "json",
        "dry-run": True,
    }


def test_ignores_positional_and_malformed_tokens():
    assert parse_flags(["input.csv", "--", "--=bad", "--verbose"]) == {
        "verbose": True
    }
