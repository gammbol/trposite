import pytest

from solver.services.ai.explanation_service import AIExplanationError, AIExplanationService


pytestmark = pytest.mark.resilience


class CorrectingModel:
    model = "fake-correcting-model"

    def __init__(self):
        self.calls = 0
        self.feedback_seen = []

    def explain(self, *, equation, variable, verified_solution, correction_feedback=None):
        self.calls += 1
        self.feedback_seen.append(correction_feedback)

        if self.calls == 1:
            expression = "C1*x"
        else:
            expression = "C1*exp(x)"

        return {
            "steps": [{"type": "text", "content": f"attempt {self.calls}"}],
            "solution": expression,
            "solution_expression": expression,
        }


class AlwaysWrongModel(CorrectingModel):
    def explain(self, **kwargs):
        self.calls += 1
        self.feedback_seen.append(kwargs.get("correction_feedback"))
        return {
            "steps": [],
            "solution": "C1*x",
            "solution_expression": "C1*x",
        }


def test_invalid_first_attempt_is_corrected_on_second(simple_equation):
    model = CorrectingModel()

    result = AIExplanationService(model=model).explain(simple_equation)

    assert result["verification"]["verified"] is True
    assert result["verification"]["attempts"] == 2
    assert model.calls == 2
    assert model.feedback_seen[0] is None
    assert "НЕ прошло" in model.feedback_seen[1]


def test_correction_loop_is_bounded(simple_equation):
    model = AlwaysWrongModel()

    with pytest.raises(AIExplanationError) as captured:
        AIExplanationService(model=model).explain(simple_equation)

    assert captured.value.attempts == AIExplanationService.MAX_ATTEMPTS
    assert model.calls == AIExplanationService.MAX_ATTEMPTS
