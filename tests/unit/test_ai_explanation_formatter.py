import pytest

from solver.services.ai.explanation_formatter import AIExplanationFormatter, ExplanationFormatError


pytestmark = pytest.mark.unit


def test_sympy_math_is_rendered_to_latex_without_llm_latex():
    formatter = AIExplanationFormatter()

    steps = formatter.format_steps(
        [
            {"type": "text", "content": "Подставляем найденные коэффициенты."},
            {
                "type": "math",
                "content": "y = C1*exp(-4*x) + exp(x)*(5*cos(x) + sin(x))/26",
            },
        ]
    )

    math = steps[1]["content"]
    assert "\\frac" in math
    assert "\\cos" in math
    assert "\\sin" in math
    assert "rac" not in math.replace("\\frac", "")
    assert "ext" not in math
    assert not any(ord(char) < 32 for char in math)


def test_llm_generated_latex_is_rejected_before_frontend():
    formatter = AIExplanationFormatter()

    with pytest.raises(ExplanationFormatError):
        formatter.format_steps(
            [
                {"type": "text", "content": "Показываем формулу."},
                {"type": "math", "content": "\\frac{1}{17} e^x \\cos(x)"},
            ]
        )


def test_json_decoded_control_characters_are_rejected():
    formatter = AIExplanationFormatter()

    with pytest.raises(ExplanationFormatError):
        formatter.format_steps(
            [
                {"type": "text", "content": "Показываем формулу."},
                {"type": "math", "content": "\x0crac(1)(17)"},
            ]
        )


def test_python_style_diff_method_is_normalized():
    formatter = AIExplanationFormatter()

    rendered = formatter.to_latex("y.diff(x) + 4*y = 0")

    assert "Derivative" not in rendered
    assert "4 y" in rendered or "4 y" in rendered.replace("\\left", "")
    assert "\\frac{d}{d x}" in rendered


def test_second_derivative_method_is_normalized():
    formatter = AIExplanationFormatter()

    rendered = formatter.to_latex("y.diff(x, 2) + y = 0")

    assert "\\frac{d^{2}}{d x^{2}}" in rendered


def test_prime_notation_is_normalized():
    formatter = AIExplanationFormatter()

    first = formatter.to_latex("y' + 4*y = 0")
    second = formatter.to_latex("y'' + y = 0")

    assert "\\frac{d}{d x}" in first
    assert "\\frac{d^{2}}{d x^{2}}" in second


def test_leibniz_notation_is_normalized():
    formatter = AIExplanationFormatter()

    rendered = formatter.to_latex("dy/dx + 4y = 0")

    assert "\\frac{d}{d x}" in rendered
    assert "4 y" in rendered


def test_y_of_x_and_implicit_multiplication_are_accepted():
    formatter = AIExplanationFormatter()

    rendered = formatter.to_latex("y(x) + 4x = 0")

    assert "y{\\left(x \\right)}" in rendered or "y{\\left(x\\right)}" in rendered
    assert "4 x" in rendered
