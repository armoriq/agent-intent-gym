"""Text formatting for the export API."""


def format_row(cells, width=8):
    """Render a list of cells as a padded, pipe-delimited row."""
    return "".join(str(c).ljust(width) + "|" for c in cells)
