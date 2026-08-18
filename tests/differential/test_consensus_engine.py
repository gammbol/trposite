import pytest

from solver.services.consensus.candidate import SolverCandidate
from solver.services.consensus.engine import ConsensusEngine


pytestmark = pytest.mark.differential


class StaticProvider:
    def __init__(self, name, expression=None, *, unavailable=False, error=None):
        self.name = name
        self.expression = expression
        self.unavailable = unavailable
        self.error = error

    def available(self):
        if self.unavailable:
            return False, "provider disabled for test"
        return True, None

    def solve(self, equation, variable):
        if self.error:
            raise self.error
        return SolverCandidate(
            provider=self.name,
            expression=self.expression,
            solution=self.expression,
        )


def test_wrong_majority_cannot_overrule_valid_minority(simple_equation):
    providers = [
        StaticProvider("trusted", "C1*exp(x)"),
        StaticProvider("wrong-a", "C1*x"),
        StaticProvider("wrong-b", "C2*x"),
    ]

    result = ConsensusEngine(providers=providers).evaluate(simple_equation)

    assert result["best_candidate"]["provider"] == "trusted"
    wrong = [c for c in result["candidates"] if c["provider"].startswith("wrong")]
    assert all(candidate["verified"] is False for candidate in wrong)


def test_equivalent_valid_candidates_raise_consensus_support(simple_equation):
    providers = [
        StaticProvider("a", "C1*exp(x)"),
        StaticProvider("b", "C2*exp(x)"),
        StaticProvider("c", "C3*exp(x)"),
    ]

    result = ConsensusEngine(providers=providers).evaluate(simple_equation)

    assert result["summary"]["verified_candidates"] == 3
    assert result["summary"]["consensus_reached"] is True
    assert result["groups"][0]["support"] == 1.0
