import pytest

from solver.services.consensus.candidate import SolverCandidate
from solver.services.consensus.grouping import CandidateGrouper
from solver.services.consensus.ranking import CandidateRanker


pytestmark = pytest.mark.unit


def _candidate(provider, expression, verified=True, score=1.0):
    return SolverCandidate(
        provider=provider,
        expression=expression,
        verification={"verified": verified, "score": score},
        status="ok" if verified else "invalid",
    )


def test_equivalent_verified_candidates_form_consensus_group():
    candidates = [
        _candidate("sympy", "C1*exp(x)"),
        _candidate("ollama", "C2*exp(x)"),
    ]

    groups = CandidateGrouper().group(candidates, "x")

    assert len(groups) == 1
    assert groups[0]["size"] == 2
    assert groups[0]["support"] == 1.0


def test_invalid_candidate_never_wins_ranking_even_with_manual_consensus():
    valid = _candidate("sympy", "C1*exp(x)", verified=True, score=0.8)
    invalid = _candidate("llm", "C1*x", verified=False, score=1.0)
    invalid.consensus_support = 1.0
    valid.consensus_support = 0.1

    ranked = CandidateRanker().rank([invalid, valid])

    assert ranked[0] is valid
    assert invalid.rank_score == 0.0
