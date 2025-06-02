from sympy import (
    symbols, Eq, Function, Derivative, simplify,
    dsolve, integrate, exp, log
)
from sympy.parsing.sympy_parser import parse_expr
from sympy.solvers.ode.ode import classify_ode
from sympy.printing.latex import latex


def make_step(content, step_type="text"):
    return {"type": step_type, "content": content}


def solve_equation(equation_str, variable_str='x'):
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

    try:
        lhs, rhs = equation_str.split('=')
        lhs_expr = parse_expr(lhs.strip(), local_dict=local_dict)
        rhs_expr = parse_expr(rhs.strip(), local_dict=local_dict)
        eq = Eq(lhs_expr, rhs_expr)
        steps.append(make_step(f"Введённое уравнение:", "text"))
        steps.append(make_step(latex(eq), "math"))
    except Exception as e:
        raise ValueError(f"Ошибка разбора уравнения: {e}")

    try:
        classification = classify_ode(eq, y)
        classification_str = ', '.join(classification)
        steps.append(make_step("Классификация уравнения:", "text"))
        steps.append(make_step(classification_str, "text"))
    except Exception:
        steps.append(make_step("Не удалось классифицировать уравнение", "text"))

    if 'separable' in classification:
        steps.append(make_step("Тип: уравнение с разделяющимися переменными", "text"))

        try:
            dy_dx = rhs_expr
            fx, gy = dy_dx.as_independent(x, as_Add=False)

            left = f"\\int \\frac{{1}}{{{latex(gy)}}} \\, dy"
            right = f"\\int {latex(fx)} \\, dx"

            int_left = integrate(1 / gy, y)
            int_right = integrate(fx, x)
            solution_latex = latex(Eq(int_left, int_right + C))

            steps.append(make_step("Разделяем переменные:", "text"))
            steps.append(make_step(f"\\frac{{1}}{{{latex(gy)}}} dy = {latex(fx)} dx", "math"))
            steps.append(make_step("Интегрируем обе части:", "text"))
            steps.append(make_step(left + " = " + latex(int_left), "math"))
            steps.append(make_step(right + " = " + latex(int_right), "math"))
            steps.append(make_step("Общее решение:", "text"))
            steps.append(make_step(solution_latex, "math"))

            return steps, solution_latex

        except Exception as e:
            steps.append(make_step(f"Ошибка разделения переменных: {e}", "text"))

    steps.append(make_step("Решаем уравнение с помощью SymPy (dsolve):", "text"))
    try:
        sol = dsolve(eq, y)
        simplified = simplify(sol.rhs)
        steps.append(make_step("Общее решение:", "text"))
        steps.append(make_step(latex(sol), "math"))
        steps.append(make_step("Упрощённое решение:", "text"))
        steps.append(make_step(f"y(x) = {latex(simplified)}", "math"))

        return steps, f"y(x) = {latex(simplified)}"

    except Exception as e:
        raise ValueError(f"Ошибка при dsolve: {e}")

