import pytest

from solver.services.verification import MultiStageVerificationEngine


pytestmark = pytest.mark.unit


def test_engine_accepts_valid_general_solution(simple_equation, simple_solution):
    result = MultiStageVerificationEngine().verify(simple_equation, simple_solution)

    assert result["verified"] is True
    assert result["symbolic"]["passed"] is True
    assert result["numerical"]["passed"] is True
    assert result["generality"]["passed"] is True
    assert result["score"] >= 0.8


def test_engine_rejects_mathematically_wrong_solution(simple_equation):
    result = MultiStageVerificationEngine().verify(simple_equation, "C1*x")

    assert result["verified"] is False
    assert result["symbolic"]["passed"] is False
    assert result["reasons"]


def test_second_order_solution_requires_two_arbitrary_constants():
    engine = MultiStageVerificationEngine()
    equation = "Derivative(y, (x, 2)) + y = 0"

    incomplete = engine.verify(equation, "C1*sin(x)")
    complete = engine.verify(equation, "C1*sin(x) + C2*cos(x)")

    assert incomplete["verified"] is False
    assert incomplete["generality"]["passed"] is False
    assert complete["verified"] is True
