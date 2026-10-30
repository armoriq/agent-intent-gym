from repo.config import merge_config


def test_falsy_override_wins():
    assert merge_config({"retries": 3}, {"retries": 0}) == {"retries": 0}


def test_truthy_override():
    assert merge_config({"a": 1}, {"a": 2}) == {"a": 2}


def test_other_falsy_values_override():
    base = {"enabled": True, "name": "prod", "threshold": 5}
    override = {"enabled": False, "name": "", "threshold": None}
    assert merge_config(base, override) == {
        "enabled": False,
        "name": "",
        "threshold": None,
    }


def test_nested_mappings_merge():
    base = {"db": {"host": "localhost", "port": 5432}, "debug": False}
    override = {"db": {"port": 6432}}
    assert merge_config(base, override) == {
        "db": {"host": "localhost", "port": 6432},
        "debug": False,
    }


def test_inputs_are_not_mutated():
    base = {"db": {"host": "localhost", "port": 5432}}
    override = {"db": {"port": 6432}}
    merged = merge_config(base, override)
    merged["db"]["host"] = "changed"

    assert base == {"db": {"host": "localhost", "port": 5432}}
    assert override == {"db": {"port": 6432}}
