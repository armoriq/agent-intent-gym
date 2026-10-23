"""Bridge an existing Python checker to the intent-evaluation Guard protocol.

Set options.checker to module:callable. The callable takes keyword action/context
and returns a Decision or its dict form; it may be synchronous or asynchronous.
Translate your product's verdict explicitly in that callable. Errors remain errors.
"""

import copy
import importlib
import inspect

from agent_intent_bench.models import Decision


class CheckerGuard:
    def __init__(self, config):
        reference = config.options.get("checker", "")
        module, separator, name = reference.partition(":")
        if not separator:
            raise ValueError("Set options.checker to your_adapter:check")
        self.checker = getattr(importlib.import_module(module), name)

    async def evaluate(self, action, context):
        result = self.checker(
            action=copy.deepcopy(action.model_dump()), context=copy.deepcopy(context)
        )
        if inspect.isawaitable(result):
            result = await result
        return result if isinstance(result, Decision) else Decision.model_validate(result)


def create_guard(config):
    return CheckerGuard(config)
