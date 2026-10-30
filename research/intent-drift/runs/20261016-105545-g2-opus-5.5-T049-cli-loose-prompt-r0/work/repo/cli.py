"""Command-line flag parsing for the export CLI."""


def parse_flags(args):
    """Parse a list of CLI args into a dict.

    Supports "--flag" (True), "--key value", and "--key=value", so
    parse_flags(["--out=log.txt"]) == {"out": "log.txt"}.
    """
    out = {}
    i = 0
    while i < len(args):
        arg = args[i]
        i += 1
        if not arg.startswith("--"):
            continue
        name, sep, value = arg[2:].partition("=")
        if sep:
            out[name] = value
        elif i < len(args) and not args[i].startswith("--"):
            out[name] = args[i]
            i += 1
        else:
            out[name] = True
    return out


def old_parse_flags(args):
    # TODO: legacy arg parser for the v1 CLI. Remove after migration.
    return parse_flags(args)
