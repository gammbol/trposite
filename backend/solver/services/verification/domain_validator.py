from sympy import S, fraction, together
from sympy.calculus.singularities import singularities


class DomainValidator:
    """Collects domain/singularity information without rejecting valid local solutions."""

    def validate(self, parsed, candidate_expression) -> dict:
        warnings = []
        candidate_singularities = []
        equation_singularities = []

        try:
            candidate_set = singularities(candidate_expression, parsed.variable)
            if candidate_set is not S.EmptySet:
                candidate_singularities = sorted(str(item) for item in candidate_set)
        except Exception:
            warnings.append("Не удалось полностью определить особенности решения.")

        try:
            _, equation_denominator = fraction(together(parsed.residual_expression))
            equation_set = singularities(1 / equation_denominator, parsed.variable)
            if equation_set is not S.EmptySet:
                equation_singularities = sorted(str(item) for item in equation_set)
        except Exception:
            warnings.append("Не удалось полностью определить область исходного ОДУ.")

        # Singularities are not automatically errors: many valid ODE solutions
        # are defined only on intervals. We expose them so the final score and UI
        # can distinguish a verified local family from an everywhere-defined one.
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
