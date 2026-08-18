import pytest

from solver.services.verification import SolutionNormalizer
from solver.services.verification.domain_validator import DomainValidator


pytestmark = pytest.mark.unit


def test_shared_equation_singularity_is_not_reported_as_extra():
    normalizer = SolutionNormalizer()
    parsed = normalizer.parse_equation("Derivative(y, x) + y/x = 0")
    candidate = normalizer.parse_candidate("C1/x").canonical_expression

    result = DomainValidator().validate(parsed, candidate)

    assert "0" in result["equation_singularities"]
    assert result["extra_singularities"] == []


def test_candidate_only_singularity_is_reported():
    normalizer = SolutionNormalizer()
    parsed = normalizer.parse_equation("Derivative(y, x) - y = 0")
    candidate = normalizer.parse_candidate("C1/(x - 1)").canonical_expression

    result = DomainValidator().validate(parsed, candidate)

    assert "1" in result["extra_singularities"]
    assert result["warnings"]
