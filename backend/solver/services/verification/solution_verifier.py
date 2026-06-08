from dataclasses import dataclass
from typing import Any

from sympy import (
    Derivative,
    Eq,
    Function,
    Symbol,
    cos,
    dsolve,
    exp,
    log,
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
    """Raised when a candidate solution cannot be parsed or verified."""


@dataclass
class ParsedEquation:
    equation: Eq
    variable: Any
    function: Any
    residual_expression: Any
    parameters: set
    order: int


class SolutionVerifier:
    """
    Independent mathematical verifier for candidate ODE solutions.

    The LLM is treated only as a candidate generator. A candidate is accepted
    only when substituting it into the original equation produces an exact
    zero residual and it contains enough free integration constants for the
    equation order.
    """

    SAMPLE_POINTS = (0.5, 1.0, 2.0, 3.0)
    NUMERICAL_TOLERANCE = 1e-8

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

    def solve_reference(self, equation_str: str, variable_str: str = "x") -> dict:
        parsed = self.parse_equation(equation_str, variable_str)

        try:
            solution = dsolve(parsed.equation, parsed.function)
            expression = simplify(solution.rhs)
        except Exception as exc:
            raise VerificationError(f"SymPy не смог получить эталонное решение: {exc}") from exc

        return {
            "equation": parsed,
            "expression": expression,
            "expression_str": str(expression),
            "solution_str": str(solution),
        }

    def parse_candidate(self, expression_str: str, variable_str: str = "x"):
        if not expression_str or not expression_str.strip():
            raise VerificationError("ИИ не вернул machine-readable выражение решения.")

        expression_str = expression_str.strip()
        if "=" in expression_str:
            expression_str = expression_str.split("=", 1)[1].strip()

        expression_str = expression_str.replace("^", "**")

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

        for index in range(1, 11):
            local_dict[f"C{index}"] = Symbol(f"C{index}")
        local_dict["C"] = Symbol("C")

        try:
            return parse_expr(expression_str, local_dict=local_dict)
        except Exception as exc:
            raise VerificationError(
                f"Не удалось разобрать solution_expression '{expression_str}': {exc}"
            ) from exc

    def _symbolic_residual(self, parsed: ParsedEquation, candidate_expression):
        try:
            substituted = parsed.residual_expression.subs(
                parsed.function,
                candidate_expression,
            ).doit()
            residual = simplify(together(trigsimp(substituted)))
        except Exception as exc:
            raise VerificationError(f"Ошибка символической подстановки: {exc}") from exc

        return residual

    def _numerical_check(self, parsed: ParsedEquation, candidate_expression, residual) -> dict:
        if residual == 0:
            return {
                "passed": True,
                "checked_points": len(self.SAMPLE_POINTS),
                "max_abs_residual": 0.0,
            }

        substitutions = {}

        for symbol in candidate_expression.free_symbols - {parsed.variable}:
            substitutions[symbol] = 1.23456789

        for symbol in parsed.parameters:
            substitutions.setdefault(symbol, 1.11111111)

        checked = 0
        max_abs_residual = 0.0

        for point in self.SAMPLE_POINTS:
            try:
                value = residual.subs(substitutions).subs(parsed.variable, point).evalf()
                if value.has(Symbol("zoo")):
                    continue
                numeric = complex(value)
                if not (abs(numeric.real) < float("inf") and abs(numeric.imag) < float("inf")):
                    continue
                max_abs_residual = max(max_abs_residual, abs(numeric))
                checked += 1
            except Exception:
                continue

        return {
            "passed": checked > 0 and max_abs_residual <= self.NUMERICAL_TOLERANCE,
            "checked_points": checked,
            "max_abs_residual": max_abs_residual if checked else None,
        }

    def verify(self, equation_str: str, candidate_expression_str: str, variable_str: str = "x") -> dict:
        parsed = self.parse_equation(equation_str, variable_str)
        candidate_expression = self.parse_candidate(candidate_expression_str, variable_str)
        residual = self._symbolic_residual(parsed, candidate_expression)

        symbolic_passed = residual == 0 or residual.equals(0) is True
        numerical = self._numerical_check(parsed, candidate_expression, residual)

        candidate_constants = (
            candidate_expression.free_symbols
            - {parsed.variable}
            - parsed.parameters
        )
        generality_passed = len(candidate_constants) >= parsed.order

        score = (
            (0.70 if symbolic_passed else 0.0)
            + (0.20 if numerical["passed"] else 0.0)
            + (0.10 if generality_passed else 0.0)
        )

        verified = symbolic_passed and generality_passed

        reasons = []
        if not symbolic_passed:
            reasons.append(
                "Подстановка решения в исходное уравнение не дала нулевую невязку."
            )
        if not generality_passed:
            reasons.append(
                "В решении недостаточно произвольных констант для общего решения "
                f"ОДУ порядка {parsed.order}."
            )

        return {
            "verified": verified,
            "score": round(score, 3),
            "symbolic": {
                "passed": symbolic_passed,
                "residual": str(residual),
            },
            "numerical": numerical,
            "generality": {
                "passed": generality_passed,
                "equation_order": parsed.order,
                "constants_found": sorted(str(symbol) for symbol in candidate_constants),
            },
            "reasons": reasons,
        }
