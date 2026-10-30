"""Command-line flag parsing for the export CLI."""


def parse_flags(args):
    """Parse a list of CLI args into a dict.

    Supports "--flag" (True), "--key value", and "--key=value", so
    parse_flags(["--out=log.txt"]) == {"out": "log.txt"}.
    """
    out = {}
    i = 0
    while i < len(args):
        argument = args[i]
        if argument.startswith("--"):
            name, separator, value = argument[2:].partition("=")

            if separator:
                out[name] = value
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                out[name] = args[i + 1]
                i += 2
                continue
            else:
                out[name] = True
        i += 1
    return out


def old_parse_flags(args):
    """Compatibility wrapper for callers using the v1 parser name."""
    return parse_flags(args)
