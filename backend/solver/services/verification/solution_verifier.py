"""Backward-compatible facade for the new multi-stage verification engine."""

from .engine import MultiStageVerificationEngine
from .normalizer import ParsedEquation, SolutionNormalizer, VerificationError


class SolutionVerifier(MultiStageVerificationEngine):
    """Compatibility name retained for older service imports."""

    pass


__all__ = [
    "SolutionVerifier",
    "MultiStageVerificationEngine",
    "SolutionNormalizer",
    "ParsedEquation",
    "VerificationError",
]
