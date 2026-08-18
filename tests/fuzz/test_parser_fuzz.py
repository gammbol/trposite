import pytest
from hypothesis import given, settings, strategies as st

from solver.services.verification import SolutionNormalizer, VerificationError


pytestmark = pytest.mark.fuzz


SAFE_ALPHABET = "xyz0123456789+-*/^().,=_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "


@given(payload=st.text(alphabet=SAFE_ALPHABET, min_size=0, max_size=100))
@settings(max_examples=150, deadline=250)
def test_random_equation_input_never_escapes_expected_error_boundary(payload):
    normalizer = SolutionNormalizer()

    try:
        result = normalizer.parse_equation(payload)
        assert result.order >= 1
    except VerificationError:
        pass


@given(payload=st.text(alphabet=SAFE_ALPHABET, min_size=0, max_size=100))
@settings(max_examples=150, deadline=250)
def test_random_candidate_input_never_escapes_expected_error_boundary(payload):
    normalizer = SolutionNormalizer()

    try:
        candidate = normalizer.parse_candidate(payload)
        assert candidate.canonical_expression is not None
    except VerificationError:
        pass
