class AISolver:
    def can_solve(self, equation):
        return True  # fallback уровень

    def solve(self, equation, variable):
        return {
            "steps": [
                {"type": "text", "content": "Решение получено с использованием AI"}
            ],
            "solution": f"AI solution for {equation}"
        }