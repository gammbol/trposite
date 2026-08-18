import pytest
from hypothesis import given, settings, strategies as st

from solver.services.verification import MultiStageVerificationEngine


pytestmark = pytest.mark.property


NON_ZERO_SMALL_INT = st.integers(min_value=-5, max_value=5).filter(lambda value: value != 0)


@given(coefficient=NON_ZERO_SMALL_INT)
@settings(max_examples=25, deadline=None)
def test_generated_first_order_exponential_families_verify(coefficient):
    equation = f"Derivative(y, x) - ({coefficient})*y = 0"
    candidate = f"C1*exp(({coefficient})*x)"

    result = MultiStageVerificationEngine().verify(equation, candidate)

    assert result["verified"] is True


@given(slope=st.integers(min_value=-8, max_value=8))
@settings(max_examples=25, deadline=None)
def test_generated_direct_integral_families_verify(slope):
    equation = f"Derivative(y, x) - ({slope})*x = 0"
    candidate = f"({slope})*x**2/2 + C1"

    result = MultiStageVerificationEngine().verify(equation, candidate)

    assert result["verified"] is True
