"""Text formatting for the export API."""


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row."""
    return "".join(f"{cell!s:<8}|" for cell in cells)
