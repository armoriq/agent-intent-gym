"""Text formatting for the export API."""

_CELL_WIDTH = 8


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row."""
    return "".join(str(c).ljust(_CELL_WIDTH) + "|" for c in cells)
