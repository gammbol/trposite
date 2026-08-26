from sympy import S, fraction, together
from sympy.calculus.singularities import singularities


class DomainValidator:
    """Collects domain/singularity information without rejecting valid local solutions."""

    @staticmethod
    def _stringify_finite_set(value):
        if value == S.EmptySet:
            return []
        try:
            return sorted(str(item) for item in value)
        except TypeError:
            # ConditionSet/ImageSet and other symbolic sets are still valuable
            # diagnostics even when they cannot be enumerated.
            return [str(value)]

    def validate(self, parsed, candidate_expression) -> dict:
        warnings = []
        candidate_singularities = []
        equation_singularities = []

        try:
            candidate_set = singularities(candidate_expression, parsed.variable)
            candidate_singularities = self._stringify_finite_set(candidate_set)
        except Exception:
            warnings.append("Не удалось полностью определить особенности решения.")

        try:
            _, equation_denominator = fraction(together(parsed.residual_expression))
            equation_set = singularities(1 / equation_denominator, parsed.variable)
            equation_singularities = self._stringify_finite_set(equation_set)
        except Exception:
            warnings.append("Не удалось полностью определить область исходного ОДУ.")

        extra = sorted(set(candidate_singularities) - set(equation_singularities))
        if extra:
            warnings.append(
                "У решения обнаружены дополнительные особые точки: " + ", ".join(extra)
            )

        return {
            "passed": True,
            "candidate_singularities": candidate_singularities,
            "equation_singularities": equation_singularities,
            "extra_singularities": extra,
            "warnings": warnings,
        }
