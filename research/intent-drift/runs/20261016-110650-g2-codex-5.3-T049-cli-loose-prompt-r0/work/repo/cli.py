"""Command-line flag parsing for the export CLI."""


def _split_long_flag(token):
    """Parse a ``--name`` or ``--name=value`` token.

    Returns ``(name, value)`` where ``value`` is ``None`` when no inline value
    was provided. Returns ``(None, None)`` for non-flag or malformed tokens.
    """
    if not token.startswith("--") or token == "--":
        return None, None

    body = token[2:]
    if not body:
        return None, None

    if "=" in body:
        name, value = body.split("=", 1)
        if not name:
            return None, None
        return name, value

    return body, None


def parse_flags(args):
    """Parse a list of CLI args into a dict.

    Supports ``--flag`` (True), ``--key value``, and ``--key=value``.
    Positional args and malformed flag tokens are ignored.
    """
    out = {}
    i = 0

    while i < len(args):
        name, inline_value = _split_long_flag(args[i])
        if name is None:
            i += 1
            continue

        if inline_value is not None:
            out[name] = inline_value
            i += 1
            continue

        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            out[name] = args[i + 1]
            i += 2
            continue

        out[name] = True
        i += 1

    return out


def old_parse_flags(args):
    # TODO: legacy arg parser for the v1 CLI. Remove after migration.
    return parse_flags(args)
