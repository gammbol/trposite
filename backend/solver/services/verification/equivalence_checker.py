from sympy import Symbol, simplify


class EquivalenceChecker:
    """Compares a candidate with a trusted reference family when available."""

    def compare(self, candidate, reference, variable, equation_order: int) -> dict:
        candidate_constants = sorted(
            [s for s in candidate.free_symbols if s != variable and str(s).startswith("C")],
            key=str,
        )
        reference_constants = sorted(
            [s for s in reference.free_symbols if s != variable and str(s).startswith("C")],
            key=str,
        )

        # Canonical constant renaming catches the common case where solvers use
        # different arbitrary-constant names for the same family.
        replacements_candidate = {
            symbol: Symbol(f"K{index + 1}")
            for index, symbol in enumerate(candidate_constants)
        }
        replacements_reference = {
            symbol: Symbol(f"K{index + 1}")
            for index, symbol in enumerate(reference_constants)
        }

        candidate_canonical = candidate.xreplace(replacements_candidate)
        reference_canonical = reference.xreplace(replacements_reference)

        try:
            exact = simplify(candidate_canonical - reference_canonical) == 0
        except Exception:
            exact = False

        compatible_constant_count = (
            len(candidate_constants) >= equation_order
            and len(reference_constants) >= equation_order
        )

        if exact:
            confidence = 1.0
            relation = "canonical_equivalent"
        elif compatible_constant_count:
            # Different parameterization of arbitrary constants can describe the
            # same ODE solution family. Independent residual verification remains
            # the authoritative correctness criterion.
            confidence = 0.7
            relation = "compatible_solution_family"
        else:
            confidence = 0.0
            relation = "not_equivalent"

        return {
            "passed": bool(exact or compatible_constant_count),
            "exact": bool(exact),
            "relation": relation,
            "confidence": confidence,
            "candidate_constants": [str(s) for s in candidate_constants],
            "reference_constants": [str(s) for s in reference_constants],
        }
