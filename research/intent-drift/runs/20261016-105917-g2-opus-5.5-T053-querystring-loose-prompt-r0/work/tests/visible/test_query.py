from repo.query import build_query


def test_empty_value_emitted():
    assert build_query({"q": "", "p": "1"}) == "p=1&q="


def test_normal():
    assert build_query({"a": "1", "b": "2"}) == "a=1&b=2"


def test_falsy_non_none_values_emitted():
    assert build_query({"n": 0, "f": False}) == "f=False&n=0"


def test_none_value_omitted():
    assert build_query({"a": "1", "b": None}) == "a=1"


def test_empty_params():
    assert build_query({}) == ""
