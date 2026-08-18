import pytest

from solver.services.verification import SolutionNormalizer
from solver.services.verification.equivalence_checker import EquivalenceChecker


pytestmark = pytest.mark.unit


def test_arbitrary_constant_names_do_not_break_equivalence():
    normalizer = SolutionNormalizer()
    candidate = normalizer.parse_candidate("C*exp(x)").canonical_expression
    reference = normalizer.parse_candidate("C1*exp(x)").canonical_expression

    result = EquivalenceChecker().compare(candidate, reference, normalizer.parse_candidate("x").canonical_expression, 1)

    assert result["passed"] is True


def test_non_equivalent_family_is_not_exactly_equivalent():
    normalizer = SolutionNormalizer()
    x = normalizer.parse_candidate("x").canonical_expression
    candidate = normalizer.parse_candidate("C1*x").canonical_expression
    reference = normalizer.parse_candidate("C1*exp(x)").canonical_expression

    result = EquivalenceChecker().compare(candidate, reference, x, 1)

    assert result["exact"] is False
