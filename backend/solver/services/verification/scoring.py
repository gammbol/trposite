class VerificationScorer:
    """Produces an explainable confidence score from independent checks."""

    WEIGHTS = {
        "symbolic": 0.45,
        "numerical": 0.20,
        "generality": 0.15,
        "equivalence": 0.10,
        "domain": 0.10,
    }

    @staticmethod
    def _clamp(value) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric))

    def calculate(self, checks: dict) -> dict:
        components = {}
        for name in self.WEIGHTS:
            check = checks.get(name, {})
            fallback = 1.0 if check.get("passed") else 0.0
            components[name] = self._clamp(check.get("confidence", fallback))

        weight_sum = sum(self.WEIGHTS.values()) or 1.0
        raw_score = sum(
            self.WEIGHTS[name] * components[name]
            for name in self.WEIGHTS
        ) / weight_sum

        return {
            "score": round(self._clamp(raw_score), 3),
            "components": {name: round(value, 3) for name, value in components.items()},
            "weights": self.WEIGHTS.copy(),
        }
