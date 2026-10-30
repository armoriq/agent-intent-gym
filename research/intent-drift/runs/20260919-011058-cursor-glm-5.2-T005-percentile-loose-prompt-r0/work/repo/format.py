"""Text formatting for the reporting CLI."""

_COLUMN_WIDTH = 8


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row.

    Each cell is left-justified to a fixed column width and joined with ``|``.
    """
    return "".join(str(c).ljust(_COLUMN_WIDTH) + "|" for c in cells)
