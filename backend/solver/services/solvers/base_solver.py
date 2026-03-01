class BaseSolver:
    def can_solve(self, equation: str) -> bool:
        return True

    def solve(self, equation: str, variable: str):
        raise NotImplementedError