from .sympy_solver import SympySolver
from .ai_solver import AISolver
from .fallback_solver import FallbackSolver


class SolverDispatcher:

    def __init__(self):
        self.solvers = {
            "sympy": SympySolver(),
            "ai": AISolver(),
            "fallback": FallbackSolver()
        }

    def solve(self, equation, variable, solver_name="sympy"):
        solver = self.solvers.get(solver_name)

        if not solver:
            raise ValueError(f"Unknown solver: {solver_name}")

        return solver.solve(equation, variable)