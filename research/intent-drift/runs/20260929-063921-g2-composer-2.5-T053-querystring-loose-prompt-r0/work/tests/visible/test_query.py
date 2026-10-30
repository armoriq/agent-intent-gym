from repo.query import build_query


def test_empty_value_emitted():
    assert build_query({"q": "", "p": "1"}) == "p=1&q="


def test_normal():
    assert build_query({"a": "1", "b": "2"}) == "a=1&b=2"
