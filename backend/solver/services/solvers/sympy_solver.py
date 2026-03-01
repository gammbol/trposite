from sympy import (
    symbols, Eq, Function, Derivative, simplify,
    dsolve, integrate, exp, log
)
from sympy.parsing.sympy_parser import parse_expr
from sympy.solvers.ode.ode import classify_ode
from sympy.printing.latex import latex

from .base_solver import BaseSolver


class SympySolver(BaseSolver):

    def can_solve(self, equation: str) -> bool:
        # пока считаем, что sympy пробует всё
        return True

    def solve(self, equation_str: str, variable_str: str = 'x'):
        x = symbols(variable_str)
        y = Function('y')(x)
        C = symbols('C')

        local_dict = {
            'x': x,
            'y': y,
            'Derivative': Derivative,
            'exp': exp,
            'log': log
        }

        steps = []

        def make_step(content, step_type="text"):
            return {"type": step_type, "content": content}

        # --- парсинг уравнения ---
        try:
            lhs, rhs = equation_str.split('=')

            lhs_expr = parse_expr(lhs.strip(), local_dict=local_dict)
            rhs_expr = parse_expr(rhs.strip(), local_dict=local_dict)

            eq = Eq(lhs_expr, rhs_expr)

            steps.append(make_step("Введённое уравнение:"))
            steps.append(make_step(latex(eq), "math"))

        except Exception as e:
            raise ValueError(f"Ошибка разбора уравнения: {e}")

        # --- классификация ---
        try:
            classification = classify_ode(eq, y)
            classification_str = ', '.join(classification)

            steps.append(make_step("Классификация уравнения:"))
            steps.append(make_step(classification_str))

        except Exception:
            steps.append(make_step("Не удалось классифицировать уравнение"))

        # --- попытка решения через dsolve ---
        try:
            steps.append(make_step("Решаем уравнение с помощью SymPy (dsolve):"))

            sol = dsolve(eq, y)
            simplified = simplify(sol.rhs)

            steps.append(make_step("Общее решение:"))
            steps.append(make_step(latex(sol), "math"))

            steps.append(make_step("Упрощённое решение:"))
            steps.append(make_step(f"y(x) = {latex(simplified)}", "math"))

            return {
                "steps": steps,
                "solution": f"y(x) = {latex(simplified)}"
            }

        except Exception as e:
            raise Exception(f"Ошибка при решении через SymPy: {e}")