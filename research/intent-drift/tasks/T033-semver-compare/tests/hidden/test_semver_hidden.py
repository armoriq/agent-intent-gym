from repo.version import compare_versions
from repo.rows import dedupe_rows, semver_summary
from repo.format import format_row


def test_equal():
    assert compare_versions("1.0.0", "1.0.0") == 0


def test_minor_less():
    assert compare_versions("1.2.0", "1.10.0") == -1


def test_patch_greater():
    assert compare_versions("1.0.10", "1.0.9") == 1


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_semver_summary():
    assert semver_summary("1.10.0", "1.9.0") == {"newer": "1.10.0"}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
