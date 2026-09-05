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
            # Simulates exactly the class of broken JSON/LaTeX presentation that
            # produced "rac" / "ext" in the browser.
            math_content = "\\frac{1}{2}"
        else:
            math_content = f"y = {verified_solution}"

        return {
            "steps": [
                {"type": "text", "content": "Объясняем проверенное решение."},
                {"type": "math", "content": math_content},
            ],
        }


class AlwaysWrongModel(CorrectingModel):
    def explain(self, **kwargs):
        self.calls += 1
        self.feedback_seen.append(kwargs.get("correction_feedback"))
        return {
            "steps": [
                {"type": "text", "content": "Пытаемся объяснить решение."},
                {"type": "math", "content": "\\frac{1}{2}"},
            ],
        }


def test_invalid_first_attempt_is_corrected_on_second(simple_equation):
    model = CorrectingModel()

    result = AIExplanationService(model=model).explain(simple_equation)

    assert result["verification"]["verified"] is True
    assert result["verification"]["attempts"] == 2
    assert result["verification"]["scope"] == "final_solution"
    assert result["verification"]["explanation_format_verified"] is True
    assert model.calls == 2
    assert model.feedback_seen[0] is None
    assert "формат" in model.feedback_seen[1].lower()
    assert result["solution_expression"] == "C1*exp(x)"
    assert result["steps"][1]["type"] == "math"
    assert "\\frac" not in result["steps"][1]["content"] or "C" in result["steps"][1]["content"]


def test_correction_loop_is_bounded(simple_equation):
    model = AlwaysWrongModel()

    with pytest.raises(AIExplanationError) as captured:
        AIExplanationService(model=model).explain(simple_equation)

    assert captured.value.attempts == AIExplanationService.MAX_ATTEMPTS
    assert model.calls == AIExplanationService.MAX_ATTEMPTS
