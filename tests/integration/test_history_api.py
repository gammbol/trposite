import pytest
from rest_framework.test import APIClient

from history.models import Solution


pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_history_endpoint_returns_newest_first():
    Solution.objects.create(equation="first", solution="a", steps=[])
    Solution.objects.create(equation="second", solution="b", steps=[])

    response = APIClient().get("/api/history/")

    assert response.status_code == 200
    payload = response.json()
    assert [row["equation"] for row in payload[:2]] == ["second", "first"]
