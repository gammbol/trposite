class CandidateRanker:
    """Ranks candidates without allowing consensus to override mathematical validity."""

    VERIFICATION_WEIGHT = 0.8
    CONSENSUS_WEIGHT = 0.2

    def rank(self, candidates: list) -> list:
        for candidate in candidates:
            if not candidate.verified:
                candidate.rank_score = 0.0
                continue

            verification_score = float(candidate.verification.get("score", 0.0))
            candidate.rank_score = round(
                self.VERIFICATION_WEIGHT * verification_score
                + self.CONSENSUS_WEIGHT * candidate.consensus_support,
                3,
            )

        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.verified,
                candidate.rank_score,
                candidate.consensus_support,
            ),
            reverse=True,
        )
