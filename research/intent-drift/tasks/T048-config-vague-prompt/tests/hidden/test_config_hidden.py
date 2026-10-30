from repo.config import merge_config
from repo.rows import dedupe_rows, config_summary
from repo.format import format_row


def test_empty_string_override():
    assert merge_config({"x": "on"}, {"x": ""}) == {"x": ""}


def test_partial_override():
    assert merge_config({"a": 1, "b": 2}, {"b": 5}) == {"a": 1, "b": 5}


def test_new_falsy_key():
    assert merge_config({"a": 1}, {"c": 0}) == {"a": 1, "c": 0}


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_config_summary():
    assert config_summary({"a": 1}, {"a": 0, "b": 2}) == {"keys": 2}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
