from .base import BaseSolver


class AlgebraSolver(BaseSolver):
    def can_solve(self, equation: str) -> bool:
        return True  # fallback

    def solve(self, equation: str, variable: str):
        return {
            "steps": [
                {"type": "text", "content": "Аналитическое решение (упрощённое)"},
            ],
            "solution": "placeholder_solution"
        }