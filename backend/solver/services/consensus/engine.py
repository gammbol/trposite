from concurrent.futures import ThreadPoolExecutor, as_completed

from solver.services.verification import MultiStageVerificationEngine, VerificationError

from .candidate import SolverCandidate
from .grouping import CandidateGrouper
from .providers import build_default_providers
from .ranking import CandidateRanker


class ConsensusEngine:
    """
    Runs independent solvers, verifies every candidate, groups equivalent valid
    solution families, and ranks them using verification strength + consensus.

    Consensus is evidence, never a correctness gate: an invalid candidate cannot
    win even if several providers return the same wrong expression.
    """

    def __init__(self, providers=None, verifier=None, grouper=None, ranker=None):
        self.verifier = verifier or MultiStageVerificationEngine()
        self.providers = providers or build_default_providers(verifier=self.verifier)
        self.grouper = grouper or CandidateGrouper(self.verifier.normalizer)
        self.ranker = ranker or CandidateRanker()

    @staticmethod
    def _failed_candidate(provider: str, status: str, message: str) -> SolverCandidate:
        return SolverCandidate(
            provider=provider,
            status=status,
            error=message,
        )

    def _run_provider(self, provider, equation: str, variable: str) -> SolverCandidate:
        available, reason = provider.available()
        if not available:
            return self._failed_candidate(provider.name, "unavailable", reason or "Unavailable")

        try:
            return provider.solve(equation, variable)
        except Exception as exc:
            return self._failed_candidate(provider.name, "error", str(exc))

    def _verify_candidate(
        self,
        candidate: SolverCandidate,
        equation: str,
        variable: str,
        reference_expression: str,
    ) -> None:
        if candidate.status != "ok" or not candidate.expression:
            return

        try:
            candidate.verification = self.verifier.verify(
                equation_str=equation,
                candidate_expression_str=candidate.expression,
                variable_str=variable,
                reference_expression_str=reference_expression,
            )
        except VerificationError as exc:
            candidate.status = "invalid"
            candidate.error = str(exc)
            candidate.verification = {
                "verified": False,
                "score": 0.0,
                "reasons": [str(exc)],
            }

        if candidate.verification and not candidate.verification.get("verified"):
            candidate.status = "invalid"

    def evaluate(self, equation: str, variable: str = "x") -> dict:
        reference = self.verifier.solve_reference(equation, variable)
        reference_expression = reference["expression_str"]

        candidates: list[SolverCandidate] = []
        workers = max(1, min(len(self.providers), 4))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._run_provider, provider, equation, variable): provider.name
                for provider in self.providers
            }
            for future in as_completed(futures):
                provider_name = futures[future]
                try:
                    candidates.append(future.result())
                except Exception as exc:
                    candidates.append(self._failed_candidate(provider_name, "error", str(exc)))

        # Stable provider ordering makes API responses and test snapshots deterministic.
        provider_order = {provider.name: index for index, provider in enumerate(self.providers)}
        candidates.sort(key=lambda candidate: provider_order.get(candidate.provider, 999))

        for candidate in candidates:
            self._verify_candidate(
                candidate,
                equation,
                variable,
                reference_expression,
            )

        groups = self.grouper.group(candidates, variable)
        ranked = self.ranker.rank(candidates)
        best = next((candidate for candidate in ranked if candidate.verified), None)

        verified_count = sum(1 for candidate in candidates if candidate.verified)
        successful_count = sum(1 for candidate in candidates if candidate.status in {"ok", "invalid"})

        return {
            "equation": equation,
            "variable": variable,
            "reference_expression": reference_expression,
            "best_candidate": best.to_dict() if best else None,
            "summary": {
                "providers_total": len(candidates),
                "providers_responded": successful_count,
                "verified_candidates": verified_count,
                "consensus_groups": len(groups),
                "consensus_reached": bool(groups and groups[0]["support"] > 0.5),
            },
            "groups": groups,
            "candidates": [candidate.to_dict() for candidate in ranked],
        }
