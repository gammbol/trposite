from sympy import symbols, Function, Eq, dsolve, simplify
from sympy.parsing.sympy_parser import parse_expr
from sympy.printing.latex import latex


def solve_equation(equation_str, variable_str='x'):
    x = symbols(variable_str)
    y = Function('y')(x)

    lhs, rhs = equation_str.split('=')

    eq = Eq(
        parse_expr(lhs),
        parse_expr(rhs)
    )

    sol = dsolve(eq, y)
    simplified = simplify(sol.rhs)

    steps = [
        {"type": "text", "content": "Решаем дифференциальное уравнение"},
        {"type": "math", "content": latex(eq)},
        {"type": "text", "content": "Общее решение:"},
        {"type": "math", "content": latex(sol)},
        {"type": "text", "content": "Упрощённый вид:"},
        {"type": "math", "content": latex(simplified)},
    ]

    return steps, f"y(x) = {latex(simplified)}"