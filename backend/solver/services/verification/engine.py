from sympy import Eq, dsolve, simplify

from .domain_validator import DomainValidator
from .equivalence_checker import EquivalenceChecker
from .normalizer import SolutionNormalizer, VerificationError
from .numerical_verifier import NumericalVerifier
from .scoring import VerificationScorer
from .symbolic_verifier import SymbolicVerifier


class MultiStageVerificationEngine:
    """
    Independent, explainable verification pipeline for ODE solution candidates.

    Correctness is gated by exact symbolic substitution and generality. Numeric,
    equivalence and domain checks provide independent evidence and diagnostics.
    """

    def __init__(
        self,
        normalizer=None,
        symbolic=None,
        numerical=None,
        equivalence=None,
        domain=None,
        scorer=None,
    ):
        self.normalizer = normalizer or SolutionNormalizer()
        self.symbolic = symbolic or SymbolicVerifier()
        self.numerical = numerical or NumericalVerifier()
        self.equivalence = equivalence or EquivalenceChecker()
        self.domain = domain or DomainValidator()
        self.scorer = scorer or VerificationScorer()

    def solve_reference(self, equation_str: str, variable_str: str = "x") -> dict:
        parsed = self.normalizer.parse_equation(equation_str, variable_str)

        try:
            raw_solution = dsolve(parsed.equation, parsed.function)

            # Some ODEs return several branches. The verifier currently needs a
            # deterministic reference family, so keep every branch for diagnostics
            # and use the first equation as the canonical reference.
            branches = raw_solution if isinstance(raw_solution, (list, tuple)) else [raw_solution]
            equations = [item for item in branches if isinstance(item, Eq)]
            if not equations:
                raise VerificationError("SymPy вернул решение в неподдерживаемом формате.")

            solution = equations[0]
            expression = simplify(solution.rhs)
        except VerificationError:
            raise
        except Exception as exc:
            raise VerificationError(f"SymPy не смог получить эталонное решение: {exc}") from exc

        return {
            "equation": parsed,
            "expression": expression,
            "expression_str": str(expression),
            "solution_str": str(solution),
            "alternatives": [str(item) for item in equations[1:]],
        }

    def verify(
        self,
        equation_str: str,
        candidate_expression_str: str,
        variable_str: str = "x",
        reference_expression_str: str | None = None,
    ) -> dict:
        parsed = self.normalizer.parse_equation(equation_str, variable_str)
        candidate = self.normalizer.parse_candidate(candidate_expression_str, variable_str)

        symbolic = self.symbolic.verify(parsed, candidate.canonical_expression)

        # Recreate the symbolic residual once so the numerical verifier operates
        # on the exact same mathematical object as the symbolic stage.
        substituted = parsed.residual_expression.subs(
            parsed.function,
            candidate.canonical_expression,
        ).doit()
        numerical = self.numerical.verify(parsed, candidate.canonical_expression, substituted)

        candidate_constants = (
            candidate.canonical_expression.free_symbols
            - {parsed.variable}
            - parsed.parameters
        )
        generality_passed = len(candidate_constants) >= parsed.order
        generality = {
            "passed": generality_passed,
            "confidence": 1.0 if generality_passed else 0.0,
            "equation_order": parsed.order,
            "constants_found": sorted(str(symbol) for symbol in candidate_constants),
            "required_constants": parsed.order,
        }

        if reference_expression_str:
            reference = self.normalizer.parse_candidate(reference_expression_str, variable_str)
            equivalence = self.equivalence.compare(
                candidate.canonical_expression,
                reference.canonical_expression,
                parsed.variable,
                parsed.order,
            )
        else:
            equivalence = {
                "passed": True,
                "exact": False,
                "relation": "reference_not_provided",
                "confidence": 0.5,
                "candidate_constants": sorted(str(s) for s in candidate.constants),
                "reference_constants": [],
            }

        domain = self.domain.validate(parsed, candidate.canonical_expression)
        domain["confidence"] = 1.0 if not domain["extra_singularities"] else 0.8

        checks = {
            "symbolic": {**symbolic, "confidence": 1.0 if symbolic["passed"] else 0.0},
            "numerical": {**numerical, "confidence": 1.0 if numerical["passed"] else 0.0},
            "generality": generality,
            "equivalence": equivalence,
            "domain": domain,
        }
        scoring = self.scorer.calculate(checks)

        # A candidate is never accepted merely because its numerical score is
        # high. Exact symbolic validity and the expected number of arbitrary
        # constants are mandatory for a general solution.
        verified = symbolic["passed"] and generality_passed

        reasons = []
        if not symbolic["passed"]:
            reasons.append(
                "Подстановка решения в исходное уравнение не дала нулевую символическую невязку."
            )
        if not numerical["passed"]:
            reasons.append("Численная проверка невязки не подтвердила решение.")
        if not generality_passed:
            reasons.append(
                "В решении недостаточно произвольных констант для общего решения "
                f"ОДУ порядка {parsed.order}."
            )
        if reference_expression_str and not equivalence["passed"]:
            reasons.append("Кандидат не согласуется с эталонным семейством решений.")
        reasons.extend(domain.get("warnings", []))

        return {
            "verified": bool(verified),
            "score": scoring["score"],
            "candidate": {
                "raw": candidate.raw,
                "canonical": str(candidate.canonical_expression),
            },
            "symbolic": checks["symbolic"],
            "numerical": checks["numerical"],
            "generality": checks["generality"],
            "equivalence": checks["equivalence"],
            "domain": checks["domain"],
            "scoring": scoring,
            "reasons": reasons,
        }
