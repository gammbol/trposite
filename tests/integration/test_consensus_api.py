import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.integration


class FakeConsensusEngine:
    def evaluate(self, equation, variable="x"):
        return {
            "equation": equation,
            "variable": variable,
            "best_candidate": {
                "provider": "sympy",
                "verified": True,
                "expression": "C1*exp(x)",
            },
            "summary": {
                "providers_total": 3,
                "providers_responded": 3,
                "verified_candidates": 2,
                "consensus_groups": 1,
                "consensus_reached": True,
            },
            "groups": [],
            "candidates": [],
        }


def test_consensus_endpoint_contract(monkeypatch):
    monkeypatch.setattr("solver.views.ConsensusEngine", lambda: FakeConsensusEngine())
    client = APIClient()

    response = client.post(
        "/api/consensus/",
        {"equation": "Derivative(y, x) - y = 0", "variable": "x"},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["consensus_reached"] is True
    assert payload["best_candidate"]["verified"] is True
