class BaseSolver:
    def can_solve(self, equation: str) -> bool:
        raise NotImplementedError

    def solve(self, equation: str, variable: str):
        raise NotImplementedError