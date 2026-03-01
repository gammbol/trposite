from .base_solver import BaseSolver

class FallbackSolver(BaseSolver):

    def solve(self, equation, variable):
        return {
            "steps": [
                {"type": "text", "content": "Не удалось решить уравнение"}
            ],
            "solution": "No solution"
        }