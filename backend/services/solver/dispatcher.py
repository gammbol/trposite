from .ode_solver import ODESolver
from .algebra_solver import AlgebraSolver


class SolverDispatcher:
    def __init__(self):
        self.solvers = [
            ODESolver(),
            AlgebraSolver()
        ]

    def solve(self, equation: str, variable: str):
        for solver in self.solvers:
            if solver.can_solve(equation):
                return solver.solve(equation, variable)

        raise Exception("No solver found")