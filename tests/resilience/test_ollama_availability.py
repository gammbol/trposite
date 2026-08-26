from unittest.mock import Mock, patch

import requests

from solver.services.consensus.providers import OllamaCandidateProvider
from solver.services.solvers.ollama_solver import OllamaSolver


def test_ollama_unavailable_is_reported_without_starting_generation():
    solver = OllamaSolver()
    with patch("solver.services.solvers.ollama_solver.requests.get") as mocked_get:
        mocked_get.side_effect = requests.ConnectionError("connection refused")
        available, reason = solver.healthcheck()

    assert available is False
    assert "недоступна" in reason.lower()


def test_provider_uses_fast_healthcheck():
    solver = Mock()
    solver.healthcheck.return_value = (False, "offline")
    provider = OllamaCandidateProvider(solver=solver)

    assert provider.available() == (False, "offline")
    solver.solve.assert_not_called()
