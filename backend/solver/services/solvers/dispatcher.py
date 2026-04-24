from .sympy_solver import SympySolver
from .ai_solver import AISolver
from .deepseek_solver import DeepSeekSolver
from .fallback_solver import FallbackSolver


class SolverDispatcher:

    def __init__(self):
        self.solvers = {
            "sympy": SympySolver(),
            "ai": AISolver(),
            "deepseek": DeepSeekSolver(),
            "fallback": FallbackSolver()
        }

    def solve(self, equation, variable, solver_name="sympy"):
        solver = self.solvers.get(solver_name)

        if not solver:
            raise ValueError(f"Unknown solver: {solver_name}")

        return solver.solve(equation, variable)