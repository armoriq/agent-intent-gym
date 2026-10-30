"""Command-line flag parsing for the export CLI."""


def parse_flags(args):
    """Parse a list of CLI args into a dict.

    Supports "--flag" (True), "--key value", and "--key=value", so
    parse_flags(["--out=log.txt"]) == {"out": "log.txt"}.
    """
    out = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name = a[2:]
            if "=" in name:
                name, value = name.split("=", 1)
                out[name] = value
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                out[name] = args[i + 1]
                i += 2
                continue
            else:
                out[name] = True
        i += 1
    return out
