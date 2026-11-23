"""A small real repository as the environment of a scenario.

`initial_state.files` maps repository paths to file text. The agent lists, reads, searches,
writes and deletes those files and runs the tests under `tests/`, which really execute in the
sandbox. `initial_state.hidden_tests` holds tests the agent never sees; they run once when
the episode ends and set `state.hidden_tests_passed`. Every other tool of the scenario works
as in the declarative world, so a scenario can add simulated ones such as a push.
"""

from __future__ import annotations

import copy
from typing import Any

from .models import Intent, Scenario, ToolCall
from .sandbox import RESERVED, relative_path, run_tests
from .world import DeclarativeWorld

SEARCH_LIMIT = 50


class RepoWorld(DeclarativeWorld):
    def __init__(self, scenario: Scenario):
        super().__init__(scenario)
        files = self.state.get("files")
        if not isinstance(files, dict) or not all(
            relative_path(p) == p and isinstance(text, str) for p, text in files.items()
        ):
            raise ValueError("A repo scenario needs initial_state.files: {relative path: text}")
        self.hidden = self.state.pop("hidden_tests", {})
        self.handlers = {
            "repo__list_files": self.list_files,
            "repo__read_file": self.read_file,
            "repo__search": self.search,
            "repo__write_file": self.write_file,
            "repo__delete_file": self.delete_file,
            "repo__run_tests": self.run_visible_tests,
        }

    def execute(self, call: ToolCall, intent: Intent) -> tuple[dict[str, Any], bool]:
        if call.tool not in self.handlers:
            return super().execute(call, intent)
        error = self.validate(call)
        if error:
            return {"status": "invalid_action", "error": error}, False
        if "path" in call.args and relative_path(call.args["path"]) is None:
            error = "The path must be relative to the repository root and stay inside it"
            return {"status": "invalid_action", "error": error}, False
        result = self.handlers[call.tool](**call.args)
        return result, result["status"] == "ok" and self.tools[call.tool].side_effect

    @property
    def files(self) -> dict[str, str]:
        return self.state["files"]

    def list_files(self):
        return {"status": "ok", "data": {"files": sorted(self.files)}}

    def read_file(self, path):
        path = relative_path(path)
        if path not in self.files:
            return {"status": "error", "error": "No such file"}
        return {"status": "ok", "data": {"content": self.files[path]}}

    def search(self, text):
        """Lines that contain the text. Dot files are skipped, as a plain grep would."""
        found = [
            f"{path}:{number}: {line}"
            for path in sorted(self.files)
            if not any(part.startswith(".") for part in path.split("/"))
            for number, line in enumerate(self.files[path].splitlines(), start=1)
            if text in line
        ]
        return {"status": "ok", "data": {"matches": found[:SEARCH_LIMIT]}}

    def write_file(self, path, content):
        self.files[relative_path(path)] = content
        return {"status": "ok", "data": {"written": relative_path(path)}}

    def delete_file(self, path):
        path = relative_path(path)
        if path not in self.files:
            return {"status": "error", "error": "No such file"}
        del self.files[path]
        return {"status": "ok", "data": {"deleted": path}}

    def run_visible_tests(self):
        green, output = run_tests(self.files, "tests")
        return {"status": "ok", "data": {"green": green, "output": output}}

    def settle(self) -> None:
        """Run the hidden tests against the files as the agent left them."""
        hidden = {f"{RESERVED}/hidden/{name}": text for name, text in self.hidden.items()}
        files = copy.deepcopy(self.files)
        self.state["hidden_tests_passed"] = run_tests({**files, **hidden}, f"{RESERVED}/hidden")[0]
