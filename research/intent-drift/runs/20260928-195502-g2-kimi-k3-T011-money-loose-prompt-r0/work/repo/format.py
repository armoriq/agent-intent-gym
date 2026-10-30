"""Text formatting for the export API."""


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row."""
    return "".join(f"{str(c):<8}|" for c in cells)
