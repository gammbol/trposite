import pytest
from django.urls import reverse

from history.models import Solution


@pytest.mark.django_db
def test_history_list_returns_newest_first(client):
    first = Solution.objects.create(equation="y.diff(x)=y", solution="a", steps=[])
    second = Solution.objects.create(equation="y.diff(x)=2*y", solution="b", steps=[])

    response = client.get(reverse("history-list"))

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [second.id, first.id]


@pytest.mark.django_db
def test_history_delete_does_not_require_csrf(client):
    entry = Solution.objects.create(equation="y.diff(x)=y", solution="a", steps=[])

    response = client.delete(reverse("history-detail", args=[entry.id]))

    assert response.status_code == 204
    assert not Solution.objects.filter(pk=entry.id).exists()


@pytest.mark.django_db
def test_history_clear(client):
    Solution.objects.create(equation="a", solution="1", steps=[])
    Solution.objects.create(equation="b", solution="2", steps=[])

    response = client.delete(reverse("history-list"))

    assert response.status_code == 200
    assert response.json()["deleted"] == 2
    assert Solution.objects.count() == 0
