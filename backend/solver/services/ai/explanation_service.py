from sympy import Eq, latex

from solver.services.solvers.ollama_solver import OllamaSolver
from solver.services.verification import MultiStageVerificationEngine, VerificationError

from .explanation_formatter import AIExplanationFormatter, ExplanationFormatError


class AIExplanationError(RuntimeError):
    def __init__(self, message, *, verification=None, attempts=0):
        super().__init__(message)
        self.verification = verification
        self.attempts = attempts


class AIExplanationService:
    """
    Explains a deterministic SymPy solution without allowing the LLM to replace it.

    SymPy is the source of truth.  The LLM receives the already verified reference
    solution and produces explanatory text plus machine-readable mathematical
    steps.  Math is parsed and rendered to LaTeX on the backend; LLM-generated
    LaTeX is never sent to the frontend.
    """

    MAX_ATTEMPTS = 3

    def __init__(self, model=None, verifier=None, formatter=None):
        self.model = model or OllamaSolver()
        self.verifier = verifier or MultiStageVerificationEngine()
        self.formatter = formatter or AIExplanationFormatter()

    def explain(self, equation: str, variable: str = "x") -> dict:
        reference = self.verifier.solve_reference(equation, variable)
        reference_expression = reference["expression_str"]

        # Verify the exact object that will be shown as the final answer.  The
        # LLM cannot replace this value later in the pipeline.
        try:
            reference_verification = self.verifier.verify(
                equation_str=equation,
                candidate_expression_str=reference_expression,
                variable_str=variable,
                reference_expression_str=reference_expression,
            )
        except VerificationError as exc:
            reference_verification = self._verification_error_payload(str(exc))

        if not reference_verification.get("verified"):
            raise AIExplanationError(
                "Эталонное решение SymPy не прошло независимую проверку; "
                "AI-объяснение не будет показано как достоверное.",
                verification=reference_verification,
                attempts=0,
            )

        reference_latex = latex(Eq(reference["equation"].function, reference["expression"]))
        feedback = None
        last_error = None

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            candidate = self.model.explain(
                equation=equation,
                variable=variable,
                verified_solution=reference_expression,
                correction_feedback=feedback,
            )

            raw_steps = candidate.get("steps", [])
            try:
                formatted_steps = self.formatter.format_steps(raw_steps, variable)
                self._validate_terminal_step(
                    raw_steps,
                    equation=equation,
                    variable=variable,
                    reference_expression=reference_expression,
                )
            except (ExplanationFormatError, VerificationError) as exc:
                last_error = str(exc)
                feedback = self._build_format_feedback(
                    error=last_error,
                    reference_expression=reference_expression,
                )
                continue

            # Backward compatibility: if an older model/prompt still returns its
            # own candidate, verify it but never display it.  New prompts do not
            # request this field at all.
            candidate_expression = candidate.get("solution_expression")
            if candidate_expression:
                try:
                    candidate_verification = self.verifier.verify(
                        equation_str=equation,
                        candidate_expression_str=candidate_expression,
                        variable_str=variable,
                        reference_expression_str=reference_expression,
                    )
                except VerificationError as exc:
                    candidate_verification = self._verification_error_payload(str(exc))

                if not candidate_verification.get("verified"):
                    last_error = "Модель попыталась изменить проверенное решение."
                    feedback = self._build_candidate_feedback(
                        candidate_expression,
                        reference_expression,
                        candidate_verification,
                    )
                    continue

            return {
                "steps": formatted_steps,
                # Both public solution fields come exclusively from SymPy.
                "solution": reference_latex,
                "solution_expression": reference_expression,
                "verification": {
                    **reference_verification,
                    "attempts": attempt,
                    "model": getattr(self.model, "model", "ollama"),
                    "scope": "final_solution",
                    "explanation_format_verified": True,
                    "explanation_terminal_verified": True,
                },
            }

        raise AIExplanationError(
            "ИИ не смог сформировать корректно отформатированное объяснение "
            f"за {self.MAX_ATTEMPTS} попытки."
            + (f" Последняя ошибка: {last_error}" if last_error else ""),
            verification={
                **reference_verification,
                "scope": "final_solution",
                "explanation_format_verified": False,
            },
            attempts=self.MAX_ATTEMPTS,
        )


    def _validate_terminal_step(
        self,
        steps,
        *,
        equation: str,
        variable: str,
        reference_expression: str,
    ) -> None:
        math_steps = [
            step for step in steps
            if isinstance(step, dict) and step.get("type") == "math"
        ]
        if not math_steps:
            raise ExplanationFormatError("Объяснение не содержит математических шагов.")

        terminal = math_steps[-1].get("content", "")
        if not isinstance(terminal, str) or terminal.count("=") != 1:
            raise ExplanationFormatError(
                "Последний математический шаг должен иметь вид y = <проверенное решение>."
            )

        lhs, rhs = (part.strip() for part in terminal.split("=", 1))
        normalized_lhs = lhs.replace(" ", "")
        if normalized_lhs not in {"y", f"y({variable})"}:
            raise ExplanationFormatError(
                "Последний математический шаг должен явно задавать y через проверенное решение."
            )

        terminal_verification = self.verifier.verify(
            equation_str=equation,
            candidate_expression_str=rhs,
            variable_str=variable,
            reference_expression_str=reference_expression,
        )
        if not terminal_verification.get("verified") or not terminal_verification.get(
            "equivalence", {}
        ).get("passed"):
            raise ExplanationFormatError(
                "Последний математический шаг не совпадает с проверенным семейством решений SymPy."
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
    def _build_format_feedback(error: str, reference_expression: str) -> str:
        return "\n".join(
            [
                "Предыдущее ОБЪЯСНЕНИЕ отклонено из-за формата математических шагов.",
                f"Причина: {error}",
                f"Проверенный ответ SymPy остаётся неизменным: y = {reference_expression}",
                "Не решай уравнение заново.",
                "Не используй LaTeX, обратные слеши, $...$ или Unicode-формулы в math.content.",
                "Используй только SymPy-синтаксис: Derivative(y, x), exp(x), sin(x), cos(x), **.",
                "Верни новый JSON только со steps.",
            ]
        )

    @staticmethod
    def _build_candidate_feedback(candidate_expression, reference_expression, verification):
        reasons = verification.get("reasons") or ["Кандидат не прошёл верификацию."]
        return "\n".join(
            [
                "Не изменяй проверенное решение SymPy.",
                f"Твой лишний candidate: {candidate_expression}",
                f"Проверенный ответ: {reference_expression}",
                *[f"- {reason}" for reason in reasons],
                "Верни только объясняющие steps; финальный ответ генерирует backend.",
            ]
        )
