from repo.config import merge_config


def test_falsy_override_wins():
    assert merge_config({"retries": 3}, {"retries": 0}) == {"retries": 0}


def test_empty_string_override_wins():
    assert merge_config({"label": "default"}, {"label": ""}) == {"label": ""}


def test_truthy_override():
    assert merge_config({"a": 1}, {"a": 2}) == {"a": 2}
