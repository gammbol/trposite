from solver.services.solvers.ollama_solver import OllamaSolver
from solver.services.verification.solution_verifier import (
    SolutionVerifier,
    VerificationError,
)


class AIExplanationError(RuntimeError):
    def __init__(self, message, *, verification=None, attempts=0):
        super().__init__(message)
        self.verification = verification
        self.attempts = attempts


class AIExplanationService:
    """
    Generates an explanation with a local LLM and independently verifies the
    solution produced by the model. Failed candidates are returned to the LLM
    with mathematical feedback for self-correction.
    """

    MAX_ATTEMPTS = 3

    def __init__(self, model=None, verifier=None):
        self.model = model or OllamaSolver()
        self.verifier = verifier or SolutionVerifier()

    def explain(self, equation: str, variable: str = "x") -> dict:
        reference = self.verifier.solve_reference(equation, variable)
        feedback = None
        last_verification = None

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            candidate = self.model.explain(
                equation=equation,
                variable=variable,
                verified_solution=reference["expression_str"],
                correction_feedback=feedback,
            )

            candidate_expression = candidate.get("solution_expression", "")

            try:
                verification = self.verifier.verify(
                    equation,
                    candidate_expression,
                    variable,
                )
            except VerificationError as exc:
                verification = {
                    "verified": False,
                    "score": 0.0,
                    "symbolic": {"passed": False, "residual": None},
                    "numerical": {
                        "passed": False,
                        "checked_points": 0,
                        "max_abs_residual": None,
                    },
                    "generality": {"passed": False},
                    "reasons": [str(exc)],
                }

            last_verification = verification

            if verification["verified"]:
                return {
                    "steps": candidate.get("steps", []),
                    "solution": candidate.get("solution", reference["expression_str"]),
                    "verification": {
                        **verification,
                        "attempts": attempt,
                        "provider": "ollama",
                        "model": self.model.model,
                    },
                }

            feedback = self._build_feedback(
                candidate_expression=candidate_expression,
                reference_expression=reference["expression_str"],
                verification=verification,
            )

        raise AIExplanationError(
            "ИИ не смог сформировать математически проверенное объяснение "
            f"за {self.MAX_ATTEMPTS} попытки.",
            verification=last_verification,
            attempts=self.MAX_ATTEMPTS,
        )

    @staticmethod
    def _build_feedback(candidate_expression, reference_expression, verification):
        residual = verification.get("symbolic", {}).get("residual")
        reasons = verification.get("reasons") or ["Кандидат не прошёл верификацию."]

        return "\n".join(
            [
                "Предыдущее решение НЕ прошло автоматическую математическую проверку.",
                f"Твоё machine-readable решение: {candidate_expression or '<empty>'}",
                f"Проверенное SymPy-решение: {reference_expression}",
                f"Невязка после подстановки: {residual}",
                "Причины:",
                *[f"- {reason}" for reason in reasons],
                "Исправь математические шаги и верни новый JSON. Не копируй ошибочный вывод.",
            ]
        )
