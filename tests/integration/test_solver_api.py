import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.integration


@pytest.fixture
def api_client():
    return APIClient()


def test_solve_endpoint_returns_fast_sympy_result(api_client):
    response = api_client.post(
        "/api/solve/",
        {"equation": "Derivative(y, x) - y = 0", "variable": "x"},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "done"
    assert payload["result"]["solution"]
    assert payload["result"]["steps"]


def test_solve_endpoint_rejects_missing_equation(api_client):
    response = api_client.post("/api/solve/", {"variable": "x"}, format="json")
    assert response.status_code == 400


def test_unknown_job_returns_404(api_client):
    response = api_client.get("/api/result/not-a-real-job/")
    assert response.status_code == 404
