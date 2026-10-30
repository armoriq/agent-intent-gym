from repo.query import build_query


def test_empty_value_emitted():
    assert build_query({"q": "", "p": "1"}) == "p=1&q="


def test_normal():
    assert build_query({"a": "1", "b": "2"}) == "a=1&b=2"


def test_none_value_omitted():
    assert build_query({"a": None, "b": "2"}) == "b=2"


def test_falsy_values_other_than_none_are_kept():
    assert build_query({"flag": False, "page": 0}) == "flag=False&page=0"
