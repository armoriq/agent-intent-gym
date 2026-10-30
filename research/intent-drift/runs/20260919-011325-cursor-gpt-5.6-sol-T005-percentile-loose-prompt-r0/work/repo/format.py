"""Text formatting for the reporting CLI."""


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row."""
    return "".join(f"{str(cell):<8}|" for cell in cells)
