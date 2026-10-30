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
        if not arg.startswith("--"):
            i += 1
            continue

        body = arg[2:]
        if "=" in body:
            name, value = body.split("=", 1)
            out[name] = value
            i += 1
            continue

        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            out[body] = args[i + 1]
            i += 2
            continue

        out[body] = True
        i += 1
    return out


def old_parse_flags(args):
    """Legacy arg parser for the v1 CLI. Remove after migration."""
    return parse_flags(args)
