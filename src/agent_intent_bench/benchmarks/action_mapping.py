"""Canonicalize browser actions for checks without executing Python or a browser."""

import ast

from ..models import Action

PARAMETERS = {
    "click": ("bid", "button", "modifiers"),
    "dblclick": ("bid", "button", "modifiers"),
    "fill": ("bid", "value"),
    "goto": ("url",),
    "scroll": ("delta_x", "delta_y"),
    "send_msg_to_user": ("text",),
    "noop": (),
    "hover": ("bid",),
    "press": ("bid", "key_comb"),
    "select_option": ("bid", "options"),
    "focus": ("bid",),
    "clear": ("bid",),
    "drag_and_drop": ("from_bid", "to_bid"),
    "go_back": (),
    "go_forward": (),
    "tab_close": (),
    "new_tab": (),
    "tab_focus": ("index",),
    "report_infeasible": ("reason",),
}


def map_browser_action(raw) -> Action:
    if not isinstance(raw, str):
        raise ValueError("Browser guard mapping requires one native action string")
    tree = ast.parse(raw, mode="exec")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Expr):
        raise ValueError("Browser checks require exactly one literal function call")
    call = tree.body[0].value
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
        raise ValueError("Only literal browser calls can be checked")
    name = call.func.id
    if name not in PARAMETERS or len(call.args) > len(PARAMETERS[name]):
        raise ValueError("Unsupported browser action or argument shape")
    args = {
        key: ast.literal_eval(value)
        for key, value in zip(PARAMETERS[name], call.args, strict=False)
    }
    for keyword in call.keywords:
        if keyword.arg not in PARAMETERS[name] or keyword.arg in args:
            raise ValueError("Unknown, duplicate, or expanded browser arguments")
        args[keyword.arg] = ast.literal_eval(keyword.value)
    return Action(tool="browser__" + name, args=args)
