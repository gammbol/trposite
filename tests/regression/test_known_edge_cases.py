import pytest

from solver.services.consensus.candidate import SolverCandidate
from solver.services.consensus.ranking import CandidateRanker
from solver.services.verification import MultiStageVerificationEngine


pytestmark = pytest.mark.regression


def test_constant_renaming_does_not_reduce_reference_equivalence(simple_equation):
    engine = MultiStageVerificationEngine()
    reference = engine.solve_reference(simple_equation)["expression_str"]
    result = engine.verify(
        simple_equation,
        "C*exp(x)",
        reference_expression_str=reference,
    )

    assert result["verified"] is True
    assert result["equivalence"]["passed"] is True


def test_missing_second_constant_is_rejected_for_second_order_ode():
    result = MultiStageVerificationEngine().verify(
        "Derivative(y, (x, 2)) - y = 0",
        "C1*exp(x)",
    )

    assert result["verified"] is False
    assert result["generality"]["required_constants"] == 2


def test_invalid_high_score_candidate_cannot_rank_above_verified_candidate():
    invalid = SolverCandidate(
        provider="invalid",
        expression="C1*x",
        status="invalid",
        verification={"verified": False, "score": 1.0},
        consensus_support=1.0,
    )
    valid = SolverCandidate(
        provider="valid",
        expression="C1*exp(x)",
        status="ok",
        verification={"verified": True, "score": 0.6},
        consensus_support=0.0,
    )

    ranked = CandidateRanker().rank([invalid, valid])

    assert ranked[0].provider == "valid"
