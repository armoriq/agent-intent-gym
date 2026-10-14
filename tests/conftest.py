import pytest

from agent_intent_bench.catalog import load_suite
from agent_intent_bench.models import RunConfig
from agent_intent_bench.session import Session


@pytest.fixture(scope="session")
def core():
    return load_suite()


@pytest.fixture
def scenario(core):
    return next(s for s in core.scenarios if s.id == "payments.approval.clean").model_copy(
        deep=True
    )


@pytest.fixture
def session(scenario):
    return Session(scenario, RunConfig(mode="unguarded"), "test-episode", 42)
