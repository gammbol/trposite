import pytest

from solver.services.verification.scoring import VerificationScorer


pytestmark = pytest.mark.unit


def test_full_confidence_produces_one():
    checks = {
        name: {"passed": True, "confidence": 1.0}
        for name in VerificationScorer.WEIGHTS
    }
    result = VerificationScorer().calculate(checks)
    assert result["score"] == 1.0


def test_symbolic_failure_has_large_score_penalty():
    checks = {
        name: {"passed": True, "confidence": 1.0}
        for name in VerificationScorer.WEIGHTS
    }
    checks["symbolic"] = {"passed": False, "confidence": 0.0}

    result = VerificationScorer().calculate(checks)
    assert result["score"] == pytest.approx(0.55, abs=1e-3)
