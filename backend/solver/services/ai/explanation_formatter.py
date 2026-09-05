import re
from string import ascii_uppercase

from sympy import Derivative, Eq, Function, Integral, Symbol, cos, exp, latex, log, sin, sqrt, symbols, tan
from sympy.core.basic import Basic
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


class ExplanationFormatError(ValueError):
    """Raised when an LLM explanation cannot be rendered safely."""


class AIExplanationFormatter:
    """
    Converts machine-readable math emitted by the LLM into LaTeX.

    The LLM is not trusted to generate LaTeX directly. Instead, this adapter
    accepts a small set of common human/Python/SymPy notations, normalizes them
    to canonical SymPy syntax, parses them symbolically, and finally lets SymPy
    generate the LaTeX that is sent to the frontend.

    This keeps the frontend readable while avoiding brittle prompt-only
    requirements such as forcing the model to spell every derivative exactly as
    ``Derivative(y, x)``.
    """

    MAX_STEPS = 40
    _TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

    def format_steps(self, steps, variable_str: str = "x") -> list[dict]:
        if not isinstance(steps, list) or not steps:
            raise ExplanationFormatError("ИИ не вернул массив steps.")
        if len(steps) > self.MAX_STEPS:
            raise ExplanationFormatError(
                f"ИИ вернул слишком много шагов ({len(steps)} > {self.MAX_STEPS})."
            )

        formatted = []
        math_count = 0
        text_count = 0
        has_russian_text = False

        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                raise ExplanationFormatError(f"Шаг {index} должен быть JSON-объектом.")

            step_type = step.get("type")
            content = step.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ExplanationFormatError(f"Шаг {index} содержит пустой content.")

            if step_type == "text":
                clean = self._clean_text(content)
                formatted.append({"type": "text", "content": clean})
                text_count += 1
                has_russian_text = has_russian_text or bool(re.search(r"[А-Яа-яЁё]", clean))
                continue

            if step_type == "math":
                formatted.append(
                    {
                        "type": "math",
                        "content": self.to_latex(content, variable_str),
                    }
                )
                math_count += 1
                continue

            raise ExplanationFormatError(
                f"Шаг {index} имеет неизвестный type={step_type!r}; разрешены text и math."
            )

        if text_count == 0 or math_count == 0:
            raise ExplanationFormatError(
                "Объяснение должно содержать и текстовые, и математические шаги."
            )
        if not has_russian_text:
            raise ExplanationFormatError("Текстовое объяснение должно быть на русском языке.")

        return formatted

    def to_latex(self, content: str, variable_str: str = "x") -> str:
        # Check the original JSON-decoded string before strip(): whitespace
        # normalization would otherwise silently erase control characters such
        # as form-feed produced by a corrupted ``\\frac`` sequence.
        if any(ord(char) < 32 and char not in "\n\r\t" for char in content):
            raise ExplanationFormatError(
                "Математический шаг содержит управляющие символы — вероятно, повреждённый LaTeX."
            )
        raw = content.strip()
        if any(ord(char) < 32 for char in raw):
            raise ExplanationFormatError(
                "Математический шаг содержит управляющие символы — вероятно, повреждённый LaTeX."
            )
        if "\\" in raw or "$" in raw:
            raise ExplanationFormatError(
                "Модель прислала LaTeX вместо машинной математической записи; "
                "требуется повторная генерация."
            )

        normalized = self._normalize_math_syntax(raw, variable_str)

        variable = symbols(variable_str)
        function = Function("y")(variable)
        local_dict = {
            variable_str: variable,
            "x": variable,
            "y": function,
            "Derivative": Derivative,
            "Integral": Integral,
            "exp": exp,
            "log": log,
            "ln": log,
            "sin": sin,
            "cos": cos,
            "tan": tan,
            "sqrt": sqrt,
        }
        for index in range(1, 21):
            local_dict[f"C{index}"] = Symbol(f"C{index}")
        local_dict["C"] = Symbol("C")
        for name in ascii_uppercase:
            local_dict.setdefault(name, Symbol(name))

        try:
            if normalized.count("=") == 1:
                lhs_raw, rhs_raw = normalized.split("=", 1)
                lhs = self._parse(lhs_raw.strip(), local_dict)
                rhs = self._parse(rhs_raw.strip(), local_dict)
                expression = Eq(lhs, rhs, evaluate=False)
            elif "=" in normalized:
                raise ExplanationFormatError(
                    "Математический шаг должен содержать не более одного знака '='."
                )
            else:
                expression = self._parse(normalized, local_dict)
        except ExplanationFormatError:
            raise
        except Exception as exc:
            raise ExplanationFormatError(
                f"Не удалось разобрать математический шаг '{raw}': {exc}"
            ) from exc

        if not isinstance(expression, Basic):
            raise ExplanationFormatError(
                f"Математический шаг '{raw}' не является SymPy-выражением."
            )

        try:
            rendered = latex(expression)
        except Exception as exc:
            raise ExplanationFormatError(
                f"Не удалось отрендерить математический шаг '{raw}': {exc}"
            ) from exc

        if not rendered or any(ord(char) < 32 for char in rendered):
            raise ExplanationFormatError("SymPy сформировал некорректное математическое представление.")
        return rendered

    def _parse(self, text: str, local_dict: dict):
        """Parse already-normalized math using a deliberately small local namespace."""
        return parse_expr(
            text,
            local_dict=local_dict,
            transformations=self._TRANSFORMATIONS,
            evaluate=False,
        )

    @classmethod
    def _normalize_math_syntax(cls, content: str, variable_str: str) -> str:
        """
        Accept common notation produced by small local LLMs and convert it to
        canonical SymPy syntax before parsing.

        Supported examples include::

            y.diff(x)          -> Derivative(y, x)
            y.diff(x, 2)       -> Derivative(y, (x, 2))
            diff(y, x)         -> Derivative(y, x)
            y'                 -> Derivative(y, x)
            y''                -> Derivative(y, (x, 2))
            dy/dx              -> Derivative(y, x)
            d2y/dx2            -> Derivative(y, (x, 2))
            y(x)               -> y
            4y                 -> 4*y   (handled by implicit multiplication)

        The normalizer intentionally does not attempt to repair LaTeX. LaTeX is
        rejected before this function is called.
        """
        variable = re.escape(variable_str)
        text = (
            content.strip()
            .replace("−", "-")
            .replace("×", "*")
            .replace("·", "*")
            .replace("^", "**")
        )

        # A model often writes y(x) even though our parser namespace already
        # binds y to the applied function y(x). Canonicalize it to simply `y`.
        text = re.sub(rf"\by\s*\(\s*{variable}\s*\)", "y", text)

        # Python/SymPy method notation: y.diff(x), y.diff(x, 2).
        method_pattern = rf"\by\s*\.\s*diff\s*\(\s*{variable}(?:\s*,\s*(\d+))?\s*\)"

        def replace_method(match):
            order = match.group(1)
            if order and int(order) > 1:
                return f"Derivative(y, ({variable_str}, {int(order)}))"
            return f"Derivative(y, {variable_str})"

        text = re.sub(method_pattern, replace_method, text, flags=re.IGNORECASE)

        # Functional diff(y, x) notation.
        diff_pattern = rf"\bdiff\s*\(\s*y\s*,\s*{variable}(?:\s*,\s*(\d+))?\s*\)"

        def replace_diff(match):
            order = match.group(1)
            if order and int(order) > 1:
                return f"Derivative(y, ({variable_str}, {int(order)}))"
            return f"Derivative(y, {variable_str})"

        text = re.sub(diff_pattern, replace_diff, text, flags=re.IGNORECASE)

        # Leibniz-style forms commonly emitted by smaller LLMs.
        text = re.sub(
            rf"\bd2y\s*/\s*d{variable}2\b",
            f"Derivative(y, ({variable_str}, 2))",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"\bdy\s*/\s*d{variable}\b",
            f"Derivative(y, {variable_str})",
            text,
            flags=re.IGNORECASE,
        )

        # Prime notation. Replace the longest form first.
        text = re.sub(
            r"\by\s*''",
            f"Derivative(y, ({variable_str}, 2))",
            text,
        )
        text = re.sub(
            r"\by\s*'",
            f"Derivative(y, {variable_str})",
            text,
        )

        # Small vocabulary aliases. `ln` is also present in local_dict, but
        # normalizing it keeps the machine representation deterministic.
        text = re.sub(r"\bln\s*\(", "log(", text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def _clean_text(content: str) -> str:
        # Collapse LLM formatting whitespace and remove non-printable characters.
        cleaned = " ".join(content.replace("\x00", " ").split())
        if not cleaned:
            raise ExplanationFormatError("Текстовый шаг оказался пустым после нормализации.")
        return cleaned
