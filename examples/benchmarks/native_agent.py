"""Native action protocol example. Scripted fixture only; replace with your own agent loop."""

import copy


class ScriptedNativeAgent:
    def __init__(self, config):
        self.actions = iter(copy.deepcopy(config.options.get("actions", [])))

    async def act(self, observation):
        try:
            return next(self.actions)
        except StopIteration:
            if observation["benchmark"] == "agentdojo":
                return {"kind": "finish", "args": {"output": ""}}
            return "send_msg_to_user('Stopping the scripted fixture.')"


def create_agent(config, seed):
    return ScriptedNativeAgent(config)
