"""Command-line flag parsing for the export CLI."""


def parse_flags(args):
    """Parse a list of CLI args into a dict.

    Supported forms:
      --flag            -> {"flag": True}
      --key value       -> {"key": "value"}
      --key=value       -> {"key": "value"}
      --key=            -> {"key": ""}

    A value taken from the next argument is only consumed when that
    argument does not itself look like a flag (i.e. does not start with
    "--"). The "--key=value" form always wins, so a value may start with
    "--" when written with "=".

    Examples:
      parse_flags(["--verbose"])            == {"verbose": True}
      parse_flags(["--out", "log.txt"])     == {"out": "log.txt"}
      parse_flags(["--out=log.txt"])        == {"out": "log.txt"}
      parse_flags(["--out=", "--verbose"])  == {"out": "", "verbose": True}
    """
    out = {}
    i = 0
    n = len(args)
    while i < n:
        a = args[i]
        if not a.startswith("--"):
            # Positional argument; ignore but keep iteration sane.
            i += 1
            continue

        name = a[2:]
        if "=" in name:
            key, _, value = name.partition("=")
            out[key] = value
            i += 1
            continue

        # Bare "--" (no name) is treated as a positional separator.
        if name == "":
            i += 1
            continue

        if i + 1 < n and not args[i + 1].startswith("--"):
            out[name] = args[i + 1]
            i += 2
            continue

        out[name] = True
        i += 1
    return out
