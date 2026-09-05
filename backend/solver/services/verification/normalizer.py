from dataclasses import dataclass
from typing import Any

from sympy import (
    Basic,
    Derivative,
    Eq,
    Function,
    Symbol,
    cos,
    exp,
    factor,
    log,
    powsimp,
    simplify,
    sin,
    sqrt,
    symbols,
    tan,
    together,
    trigsimp,
)
from sympy.parsing.sympy_parser import parse_expr
from sympy.solvers.deutils import ode_order


class VerificationError(ValueError):
    """Raised when an equation or candidate cannot be normalized."""


@dataclass
class ParsedEquation:
    equation: Eq
    variable: Any
    function: Any
    residual_expression: Any
    parameters: set
    order: int


@dataclass
class NormalizedCandidate:
    raw: str
    expression: Any
    canonical_expression: Any
    constants: set


class SolutionNormalizer:
    """Converts user/solver output into a stable SymPy representation."""

    def parse_equation(self, equation_str: str, variable_str: str = "x") -> ParsedEquation:
        if equation_str.count("=") != 1:
            raise VerificationError("Уравнение должно содержать ровно один знак '='.")

        variable = symbols(variable_str)
        function = Function("y")(variable)
        local_dict = {
            variable_str: variable,
            "x": variable,
            "y": function,
            "Derivative": Derivative,
            "exp": exp,
            "log": log,
            "sin": sin,
            "cos": cos,
            "tan": tan,
            "sqrt": sqrt,
        }
        try:
            lhs_raw, rhs_raw = equation_str.split("=", 1)
            lhs = parse_expr(lhs_raw.strip(), local_dict=local_dict)
            rhs = parse_expr(rhs_raw.strip(), local_dict=local_dict)
        except Exception as exc:
            raise VerificationError(f"Не удалось разобрать исходное уравнение: {exc}") from exc

        equation = Eq(lhs, rhs)
        residual_expression = lhs - rhs
        parameters = residual_expression.free_symbols - {variable}
        try:
            order = int(ode_order(equation, function))
        except Exception:
            order = 1

        return ParsedEquation(
            equation=equation,
            variable=variable,
            function=function,
            residual_expression=residual_expression,
            parameters=parameters,
            order=max(order, 1),
        )

    def parse_candidate(self, expression_str: str, variable_str: str = "x") -> NormalizedCandidate:
        if not expression_str or not expression_str.strip():
            raise VerificationError("Решатель не вернул machine-readable выражение решения.")

        original = expression_str.strip()
        normalized = original
        if "=" in normalized:
            normalized = normalized.split("=", 1)[1].strip()
        normalized = normalized.replace("^", "**")
        variable = symbols(variable_str)

        local_dict = {
            variable_str: variable,
            "x": variable,
            "exp": exp,
            "log": log,
            "sin": sin,
            "cos": cos,
            "tan": tan,
            "sqrt": sqrt,
        }

        for index in range(1, 21):
            local_dict[f"C{index}"] = Symbol(f"C{index}")
        local_dict["C"] = Symbol("C")

        try:
            expression = parse_expr(normalized, local_dict=local_dict)
        except Exception as exc:
            raise VerificationError(
                f"Не удалось разобрать solution_expression '{original}': {exc}"
            ) from exc

        # parse_expr can resolve short names such as "N" or "O" to SymPy
        # functions/classes instead of mathematical expressions.  Those values
        # are valid Python objects, but they are not candidates that the
        # verification pipeline can safely inspect (e.g. via free_symbols).
        if not isinstance(expression, Basic):
            raise VerificationError(
                f"solution_expression '{original}' не является математическим выражением."
            )

        canonical = self.canonicalize(expression)
        if not isinstance(canonical, Basic):
            raise VerificationError(
                f"solution_expression '{original}' не удалось нормализовать как математическое выражение."
            )

        constants = {
            symbol
            for symbol in canonical.free_symbols
            if symbol != variable and str(symbol).startswith("C")
        }
        return NormalizedCandidate(
            raw=original,
            expression=expression,
            canonical_expression=canonical,
            constants=constants,
        )

    @staticmethod
    def canonicalize(expression):
        """Apply deterministic simplifications without changing the solution family."""
        try:
            expression = together(expression)
            expression = trigsimp(expression)
            expression = powsimp(expression, force=True)
            expression = factor(expression)
            expression = simplify(expression)
        except Exception:
            # Normalization should not make otherwise parseable candidates unusable.
            pass
        return expression
