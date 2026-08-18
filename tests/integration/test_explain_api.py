import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.integration


class FakeExplanationService:
    def explain(self, equation, variable="x"):
        return {
            "steps": [{"type": "text", "content": "verified explanation"}],
            "solution": "y=C_1e^x",
            "solution_expression": "C1*exp(x)",
            "verification": {"verified": True, "attempts": 1, "score": 1.0},
        }


def test_explain_endpoint_contract_without_real_llm(monkeypatch):
    monkeypatch.setattr("solver.views.AIExplanationService", lambda: FakeExplanationService())
    client = APIClient()

    response = client.post(
        "/api/explain/",
        {"equation": "Derivative(y, x) - y = 0", "variable": "x"},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["verification"]["verified"] is True
    assert payload["solution_expression"] == "C1*exp(x)"
