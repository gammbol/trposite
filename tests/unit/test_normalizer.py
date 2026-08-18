import pytest

from solver.services.verification import SolutionNormalizer, VerificationError


pytestmark = pytest.mark.unit


def test_parse_first_order_equation_detects_order_and_function():
    normalizer = SolutionNormalizer()
    parsed = normalizer.parse_equation("Derivative(y, x) - y = 0", "x")

    assert parsed.order == 1
    assert str(parsed.variable) == "x"
    assert str(parsed.function) == "y(x)"


def test_parse_second_order_equation_detects_order():
    parsed = SolutionNormalizer().parse_equation(
        "Derivative(y, (x, 2)) + y = 0",
        "x",
    )
    assert parsed.order == 2


def test_candidate_accepts_caret_and_normalizes_constants():
    candidate = SolutionNormalizer().parse_candidate("y(x) = C1*x^2", "x")

    assert str(candidate.canonical_expression) == "C1*x**2"
    assert {str(symbol) for symbol in candidate.constants} == {"C1"}


def test_equation_requires_exactly_one_equals_sign():
    normalizer = SolutionNormalizer()

    with pytest.raises(VerificationError):
        normalizer.parse_equation("Derivative(y, x) - y")

    with pytest.raises(VerificationError):
        normalizer.parse_equation("y = x = 1")


def test_empty_candidate_is_rejected():
    with pytest.raises(VerificationError):
        SolutionNormalizer().parse_candidate("   ", "x")
