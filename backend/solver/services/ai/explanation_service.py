from solver.services.solvers.ollama_solver import OllamaSolver
from solver.services.verification import MultiStageVerificationEngine, VerificationError


class AIExplanationError(RuntimeError):
    def __init__(self, message, *, verification=None, attempts=0):
        super().__init__(message)
        self.verification = verification
        self.attempts = attempts


class AIExplanationService:
    """
    Generates an explanation with a local LLM and independently verifies every
    candidate through the multi-stage mathematical verification engine.

    Failed candidates are returned to the model with precise diagnostic data,
    forming a bounded self-correction loop.
    """

    MAX_ATTEMPTS = 3

    def __init__(self, model=None, verifier=None):
        self.model = model or OllamaSolver()
        self.verifier = verifier or MultiStageVerificationEngine()

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
                    equation_str=equation,
                    candidate_expression_str=candidate_expression,
                    variable_str=variable,
                    reference_expression_str=reference["expression_str"],
                )
            except VerificationError as exc:
                verification = self._verification_error_payload(str(exc))

            last_verification = verification

            if verification["verified"]:
                return {
                    "steps": candidate.get("steps", []),
                    "solution": candidate.get("solution", ""),
                    "solution_expression": candidate_expression,
                    "verification": {
                        **verification,
                        "attempts": attempt,
                        "model": getattr(self.model, "model", "ollama"),
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
    def _verification_error_payload(message: str) -> dict:
        return {
            "verified": False,
            "score": 0.0,
            "symbolic": {"passed": False, "residual": None, "confidence": 0.0},
            "numerical": {
                "passed": False,
                "checked_points": 0,
                "skipped_points": 0,
                "max_abs_residual": None,
                "confidence": 0.0,
            },
            "generality": {"passed": False, "confidence": 0.0},
            "equivalence": {"passed": False, "confidence": 0.0},
            "domain": {"passed": False, "confidence": 0.0, "warnings": []},
            "scoring": {"score": 0.0, "components": {}, "weights": {}},
            "reasons": [message],
        }

    @staticmethod
    def _build_feedback(candidate_expression, reference_expression, verification):
        symbolic = verification.get("symbolic", {})
        numerical = verification.get("numerical", {})
        generality = verification.get("generality", {})
        equivalence = verification.get("equivalence", {})
        domain = verification.get("domain", {})
        reasons = verification.get("reasons") or ["Кандидат не прошёл верификацию."]

        return "\n".join(
            [
                "Предыдущее решение НЕ прошло многоуровневую автоматическую проверку.",
                f"Твоё machine-readable решение: {candidate_expression or '<empty>'}",
                f"Проверенное SymPy-решение: {reference_expression}",
                f"Итоговый confidence score: {verification.get('score', 0.0)}",
                f"Символическая невязка: {symbolic.get('residual')}",
                f"Symbolic passed: {symbolic.get('passed')}",
                f"Numerical passed: {numerical.get('passed')}; "
                f"max residual: {numerical.get('max_abs_residual')}",
                f"Generality passed: {generality.get('passed')}; "
                f"constants: {generality.get('constants_found')}",
                f"Reference relation: {equivalence.get('relation')}",
                f"Domain warnings: {domain.get('warnings')}",
                "Причины отклонения:",
                *[f"- {reason}" for reason in reasons],
                "Исправь математические шаги и верни новый JSON. "
                "Не повторяй отклонённое решение без исправлений.",
            ]
        )
