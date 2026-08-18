import pytest

from solver.services.verification import SolutionNormalizer
from solver.services.verification.symbolic_verifier import SymbolicVerifier


pytestmark = pytest.mark.unit


def _verify(expression):
    normalizer = SolutionNormalizer()
    parsed = normalizer.parse_equation("Derivative(y, x) - y = 0")
    candidate = normalizer.parse_candidate(expression)
    return SymbolicVerifier().verify(parsed, candidate.canonical_expression)


def test_exact_substitution_accepts_valid_solution():
    result = _verify("C1*exp(x)")
    assert result["passed"] is True
    assert result["residual"] == "0"


def test_exact_substitution_rejects_invalid_solution():
    result = _verify("C1*x")
    assert result["passed"] is False
    assert result["residual"] != "0"
