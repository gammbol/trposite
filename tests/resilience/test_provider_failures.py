import pytest

from solver.services.consensus.candidate import SolverCandidate
from solver.services.consensus.engine import ConsensusEngine
from solver.services.consensus.providers import OpenAICompatibleCandidateProvider


pytestmark = pytest.mark.resilience


class GoodProvider:
    name = "good"

    def available(self):
        return True, None

    def solve(self, equation, variable):
        return SolverCandidate(provider=self.name, expression="C1*exp(x)")


class TimeoutProvider:
    name = "timeout"

    def available(self):
        return True, None

    def solve(self, equation, variable):
        raise TimeoutError("simulated provider timeout")


class DisabledProvider:
    name = "disabled"

    def available(self):
        return False, "simulated maintenance"

    def solve(self, equation, variable):
        raise AssertionError("unavailable provider must not be called")


def test_consensus_survives_timeout_and_unavailable_provider(simple_equation):
    result = ConsensusEngine(
        providers=[GoodProvider(), TimeoutProvider(), DisabledProvider()]
    ).evaluate(simple_equation)

    assert result["best_candidate"]["provider"] == "good"
    by_provider = {item["provider"]: item for item in result["candidates"]}
    assert by_provider["timeout"]["status"] == "error"
    assert by_provider["disabled"]["status"] == "unavailable"


def test_cloud_provider_without_key_is_explicitly_unavailable():
    provider = OpenAICompatibleCandidateProvider(
        name="test-provider",
        model="unused",
        api_key=None,
    )

    available, reason = provider.available()

    assert available is False
    assert "not configured" in reason
