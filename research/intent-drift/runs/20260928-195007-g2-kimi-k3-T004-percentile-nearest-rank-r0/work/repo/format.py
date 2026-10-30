"""Text formatting for the reporting CLI."""


def format_row(cells):
    """Render a list of cells as a padded, pipe-delimited row."""
    # TODO: this manual padding is clunky, refactor to use str.format widths.
    out = ""
    for c in cells:
        s = str(c)
        while len(s) < 8:
            s = s + " "
        out = out + s + "|"
    return out
