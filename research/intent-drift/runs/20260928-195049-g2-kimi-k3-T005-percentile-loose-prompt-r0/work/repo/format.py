"""Text formatting for the reporting CLI."""

CELL_WIDTH = 8


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row."""
    return "".join(str(c).ljust(CELL_WIDTH) + "|" for c in cells)
