from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SolverCandidate:
    provider: str
    expression: str | None = None
    solution: str | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error: str | None = None
    verification: dict[str, Any] | None = None
    group_id: int | None = None
    consensus_support: float = 0.0
    rank_score: float = 0.0

    @property
    def verified(self) -> bool:
        return bool(self.verification and self.verification.get("verified"))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["verified"] = self.verified
        return payload
