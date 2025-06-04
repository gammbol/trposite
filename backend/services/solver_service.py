from services.solver import solve_equation

def solve(equation: str, variable: str = "x"):
    """
    High-level solver service.
    Acts as an abstraction layer for equation solving logic.
    """

    steps, solution = solve_equation(equation, variable)

    return {
        "steps": steps,
        "solution": solution
    }