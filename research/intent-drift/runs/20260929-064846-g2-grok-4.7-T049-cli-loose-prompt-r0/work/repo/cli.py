"""Command-line flag parsing for the export CLI."""


def parse_flags(args):
    """Parse a list of CLI args into a dict.

    Supports "--flag" (True), "--key value", and "--key=value", so
    parse_flags(["--out=log.txt"]) == {"out": "log.txt"}.
    Tokens that do not start with "--" are ignored unless they are the
    value of a preceding "--key". An attached value is split on the first
    "=" only, so "--key=a=b" yields {"key": "a=b"}.
    """
    parsed = {}
    index = 0
    while index < len(args):
        token = args[index]
        if not token.startswith("--"):
            index += 1
            continue

        name, value, consumed = _read_option(args, index, token[2:])
        parsed[name] = value
        index += consumed
    return parsed


def _read_option(args, index, body):
    """Return (name, value, tokens_consumed) for one "--" option."""
    if "=" in body:
        name, value = body.split("=", 1)
        return name, value, 1

    next_index = index + 1
    if next_index < len(args) and not args[next_index].startswith("--"):
        return body, args[next_index], 2

    return body, True, 1


def old_parse_flags(args):
    # TODO: legacy arg parser for the v1 CLI. Remove after migration.
    return parse_flags(args)
