import json

from solver.services.consensus.providers import OpenAICompatibleCandidateProvider
from solver.services.solvers.ollama_solver import OllamaSolver
from solver.services.verification.numerical_verifier import NumericalVerifier
from solver.services.verification.scoring import VerificationScorer


def test_ollama_json_parser_handles_braces_inside_string_values():
    solver = OllamaSolver()
    payload = {
        "steps": [
            {
                "type": "math",
                "content": r"\\left\\{ y = C_1 e^x \\right\\}",
            }
        ],
        "solution": r"y=C_1e^x",
        "solution_expression": "C1*exp(x)",
    }
    text = "prefix\n" + json.dumps(payload) + "\nsuffix {not json}"
    assert solver.extract_json(text) == payload


def test_openai_compatible_json_parser_handles_trailing_text_and_braces_in_strings():
    payload = {
        "steps": [{"type": "text", "content": "consider set {x > 0}"}],
        "solution": "ok",
        "solution_expression": "C1*exp(x)",
    }
    content = "Model output:\n" + json.dumps(payload) + "\nDone."
    assert OpenAICompatibleCandidateProvider._parse_json(content) == payload


def test_verification_score_is_always_bounded():
    scorer = VerificationScorer()
    checks = {
        "symbolic": {"passed": True, "confidence": 5},
        "numerical": {"passed": True, "confidence": 2},
        "generality": {"passed": True, "confidence": 1},
        "equivalence": {"passed": True, "confidence": 4},
        "domain": {"passed": True, "confidence": -3},
    }
    result = scorer.calculate(checks)
    assert 0.0 <= result["score"] <= 1.0
    assert all(0.0 <= value <= 1.0 for value in result["components"].values())


def test_numerical_verifier_requires_more_than_one_valid_sample():
    verifier = NumericalVerifier()
    assert verifier.MIN_CHECKED_POINTS > 1
