import json

import pytest

from solver.services.consensus.providers import OpenAICompatibleCandidateProvider


pytestmark = pytest.mark.fuzz


def test_json_parser_accepts_clean_payload():
    payload = '{"solution_expression":"C1*exp(x)","steps":[],"solution":"ok"}'
    parsed = OpenAICompatibleCandidateProvider._parse_json(payload)
    assert parsed["solution_expression"] == "C1*exp(x)"


def test_json_parser_extracts_first_balanced_object_from_surrounding_text():
    payload = (
        "model preamble\n"
        '{"solution_expression":"C1*exp(x)","steps":[],"solution":"ok"}'
        "\nmodel epilogue"
    )
    parsed = OpenAICompatibleCandidateProvider._parse_json(payload)
    assert parsed["solution_expression"] == "C1*exp(x)"


def test_json_parser_rejects_incomplete_object():
    with pytest.raises((ValueError, json.JSONDecodeError)):
        OpenAICompatibleCandidateProvider._parse_json('{"solution_expression":"C1*exp(x)"')
