import json
import os
from abc import ABC, abstractmethod

from solver.services.solvers.ollama_solver import OllamaSolver
from solver.services.verification import MultiStageVerificationEngine

from .candidate import SolverCandidate


class CandidateProvider(ABC):
    name = "unknown"

    @abstractmethod
    def available(self) -> tuple[bool, str | None]:
        raise NotImplementedError

    @abstractmethod
    def solve(self, equation: str, variable: str) -> SolverCandidate:
        raise NotImplementedError


class SymPyCandidateProvider(CandidateProvider):
    name = "sympy"

    def __init__(self, verifier=None):
        self.verifier = verifier or MultiStageVerificationEngine()

    def available(self):
        return True, None

    def solve(self, equation: str, variable: str) -> SolverCandidate:
        reference = self.verifier.solve_reference(equation, variable)
        return SolverCandidate(
            provider=self.name,
            expression=reference["expression_str"],
            solution=reference["solution_str"],
            steps=[],
        )


class OllamaCandidateProvider(CandidateProvider):
    name = "ollama"

    def __init__(self, solver=None):
        self.solver = solver or OllamaSolver()

    def available(self):
        return self.solver.healthcheck()

    def solve(self, equation: str, variable: str) -> SolverCandidate:
        payload = self.solver.solve(equation, variable)
        expression = payload.get("solution_expression")
        if not expression:
            raise ValueError("Ollama не вернула solution_expression.")

        return SolverCandidate(
            provider=self.name,
            expression=expression,
            solution=payload.get("solution"),
            steps=payload.get("steps", []),
        )


class OpenAICompatibleCandidateProvider(CandidateProvider):
    """Strict machine-readable candidate provider for OpenAI-compatible APIs."""

    def __init__(self, *, name, model, api_key, base_url=None):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = float(os.getenv("LLM_PROVIDER_TIMEOUT", "45"))
        self.max_retries = int(os.getenv("LLM_PROVIDER_MAX_RETRIES", "1"))

    def available(self):
        if not self.api_key:
            return False, f"API key for {self.name} is not configured."
        return True, None

    @staticmethod
    def _prompt(equation: str, variable: str) -> str:
        return f"""
Solve the differential equation below independently.

Equation:
{equation}

Independent variable: {variable}

Return ONLY valid JSON:
{{
  "steps": [
    {{"type": "text", "content": "one mathematical action"}},
    {{"type": "math", "content": "LaTeX formula"}}
  ],
  "solution": "LaTeX general solution",
  "solution_expression": "right-hand side of y({variable}) in SymPy syntax"
}}

The field solution_expression is mandatory and is parsed automatically.
Use ** for powers, exp(), log(), sin(), cos(), and arbitrary constants C1, C2, ...
Do not include y({variable})= in solution_expression.
"""

    @staticmethod
    def _parse_json(content: str) -> dict:
        if not content or not content.strip():
            raise ValueError("LLM response is empty.")

        stripped = content.strip()
        try:
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        for index, char in enumerate(stripped):
            if char != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(stripped[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload

        raise ValueError("LLM response does not contain a complete JSON object.")

    def solve(self, equation: str, variable: str) -> SolverCandidate:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Package 'openai' is not installed.") from exc

        kwargs = {
            "api_key": self.api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        client = OpenAI(**kwargs)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a differential-equation solver. Return only "
                        "the requested machine-readable JSON."
                    ),
                },
                {"role": "user", "content": self._prompt(equation, variable)},
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content or ""
        payload = self._parse_json(content)
        expression = payload.get("solution_expression")
        if not expression:
            raise ValueError(f"{self.name} did not return solution_expression.")

        return SolverCandidate(
            provider=self.name,
            expression=expression,
            solution=payload.get("solution"),
            steps=payload.get("steps", []),
        )


def build_default_providers(verifier=None) -> list[CandidateProvider]:
    verifier = verifier or MultiStageVerificationEngine()

    try:
        from django.conf import settings
    except ImportError:
        settings = None

    def setting(name):
        if settings is None:
            return None
        try:
            return getattr(settings, name, None)
        except Exception:
            return None

    openai_key = setting("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    deepseek_key = (
        setting("DEEPSEEK_API_KEY")
        or setting("DEEP_SEEK_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("DEEP_SEEK_API_KEY")
    )

    return [
        SymPyCandidateProvider(verifier=verifier),
        OllamaCandidateProvider(),
        OpenAICompatibleCandidateProvider(
            name="openai",
            model="gpt-4.1-mini",
            api_key=openai_key,
        ),
        OpenAICompatibleCandidateProvider(
            name="deepseek",
            model="deepseek-chat",
            api_key=deepseek_key,
            base_url="https://api.deepseek.com",
        ),
    ]
