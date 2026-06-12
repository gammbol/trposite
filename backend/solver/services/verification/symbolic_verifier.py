from sympy import simplify, together, trigsimp

from .normalizer import ParsedEquation, VerificationError


class SymbolicVerifier:
    """Exact substitution-based verification of an ODE candidate."""

    def verify(self, parsed: ParsedEquation, candidate_expression) -> dict:
        try:
            substituted = parsed.residual_expression.subs(
                parsed.function,
                candidate_expression,
            ).doit()
            residual = simplify(together(trigsimp(substituted)))
        except Exception as exc:
            raise VerificationError(f"Ошибка символической подстановки: {exc}") from exc

        passed = residual == 0 or residual.equals(0) is True

        return {
            "passed": bool(passed),
            "residual": str(residual),
            "method": "exact_substitution",
        }
