class VerificationScorer:
    """Produces an explainable confidence score from independent checks."""

    WEIGHTS = {
        "symbolic": 0.45,
        "numerical": 0.20,
        "generality": 0.15,
        "equivalence": 0.10,
        "domain": 0.10,
    }

    def calculate(self, checks: dict) -> dict:
        components = {
            name: float(checks[name].get("confidence", 1.0 if checks[name].get("passed") else 0.0))
            for name in self.WEIGHTS
        }

        raw_score = sum(
            self.WEIGHTS[name] * components[name]
            for name in self.WEIGHTS
        )

        return {
            "score": round(raw_score, 3),
            "components": {name: round(value, 3) for name, value in components.items()},
            "weights": self.WEIGHTS.copy(),
        }
