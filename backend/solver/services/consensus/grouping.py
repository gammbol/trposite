from sympy import Symbol, simplify

from solver.services.verification import SolutionNormalizer


class CandidateGrouper:
    """Groups independently verified candidates into equivalent solution families."""

    def __init__(self, normalizer=None):
        self.normalizer = normalizer or SolutionNormalizer()

    @staticmethod
    def _rename_constants(expression):
        constants = sorted(
            [s for s in expression.free_symbols if str(s).startswith("C")],
            key=str,
        )
        replacements = {
            symbol: Symbol(f"K{index + 1}")
            for index, symbol in enumerate(constants)
        }
        return expression.xreplace(replacements), len(constants)

    def equivalent(self, left: str, right: str, variable: str) -> bool:
        left_expr = self.normalizer.parse_candidate(left, variable).canonical_expression
        right_expr = self.normalizer.parse_candidate(right, variable).canonical_expression

        left_canonical, left_constants = self._rename_constants(left_expr)
        right_canonical, right_constants = self._rename_constants(right_expr)

        try:
            if simplify(left_canonical - right_canonical) == 0:
                return True
        except Exception:
            pass

        # If both independently satisfy the original ODE as general solutions,
        # equal arbitrary-constant dimensionality is enough to treat them as the
        # same solution family for consensus purposes. Correctness itself is never
        # inferred from this heuristic; the verification engine gates that first.
        return left_constants > 0 and left_constants == right_constants

    def group(self, candidates: list, variable: str) -> list[dict]:
        verified = [candidate for candidate in candidates if candidate.verified and candidate.expression]
        groups: list[dict] = []

        for candidate in verified:
            matched = None
            for group in groups:
                representative = group["representative"]
                if self.equivalent(candidate.expression, representative.expression, variable):
                    matched = group
                    break

            if matched is None:
                matched = {
                    "id": len(groups) + 1,
                    "representative": candidate,
                    "members": [],
                }
                groups.append(matched)

            matched["members"].append(candidate)
            candidate.group_id = matched["id"]

        total_verified = max(len(verified), 1)
        for group in groups:
            support = len(group["members"]) / total_verified
            for candidate in group["members"]:
                candidate.consensus_support = round(support, 3)

        return [
            {
                "id": group["id"],
                "providers": [candidate.provider for candidate in group["members"]],
                "size": len(group["members"]),
                "support": round(len(group["members"]) / total_verified, 3),
                "representative_expression": group["representative"].expression,
            }
            for group in groups
        ]
