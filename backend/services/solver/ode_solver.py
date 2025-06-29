from sympy import symbols, Function, Eq, dsolve
from sympy.parsing.sympy_parser import parse_expr
from sympy.printing.latex import latex

from .base import BaseSolver


class ODESolver(BaseSolver):
    def can_solve(self, equation: str) -> bool:
        return "Derivative" in equation or "y" in equation

    def solve(self, equation: str, variable: str):
        x = symbols(variable)
        y = Function('y')(x)

        lhs, rhs = equation.split("=")

        eq = Eq(
            parse_expr(lhs),
            parse_expr(rhs)
        )

        sol = dsolve(eq, y)

        return {
            "steps": [
                {"type": "text", "content": "Решение ОДУ через dsolve"},
                {"type": "math", "content": latex(sol)}
            ],
            "solution": latex(sol)
        }