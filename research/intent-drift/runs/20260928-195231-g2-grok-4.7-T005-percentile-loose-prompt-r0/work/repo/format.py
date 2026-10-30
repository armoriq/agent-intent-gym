"""Text formatting for the reporting CLI."""

_CELL_WIDTH = 8


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row."""
    width = _CELL_WIDTH
    return "".join(f"{str(cell):<{width}}|" for cell in cells)
