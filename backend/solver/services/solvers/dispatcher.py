from .sympy_solver import SympySolver
from .fallback_solver import FallbackSolver
from .ai_solver import AISolver


class SolverDispatcher:
    def __init__(self):
        self.solvers = [
            SympySolver(),
            AISolver(),
            FallbackSolver(),
        ]

    def solve(self, equation, variable):
        for solver in self.solvers:
            try:
                return solver.solve(equation, variable)
            except Exception:
                continue

        raise Exception("No solver available")