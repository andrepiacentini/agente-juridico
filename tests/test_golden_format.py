"""Formato da bateria de avaliação (T9.1, D61): o arquivo carrega e todo caso segue a estrutura documentada nele."""

from pathlib import Path

import pytest
import yaml

GOLDEN_PATH = Path(__file__).parent / "golden.yaml"
CASE_KEYS = {"id", "description", "source", "turns"}
TURN_KEYS = {"ask", "must_call", "must_contain", "must_not_contain"}


def golden_cases() -> list[dict]:
    return yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8"))["cases"]


def test_the_golden_file_has_at_least_one_case() -> None:
    assert golden_cases()


def test_case_ids_are_unique() -> None:
    ids = [case["id"] for case in golden_cases()]

    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("case", golden_cases(), ids=lambda case: case["id"])
def test_every_case_follows_the_documented_structure(case: dict) -> None:
    assert set(case) <= CASE_KEYS and {"id", "turns"} <= set(case)
    assert case["turns"], "caso sem perguntas"
    for turn in case["turns"]:
        assert set(turn) <= TURN_KEYS and isinstance(turn["ask"], str) and turn["ask"].strip()
        assert all(isinstance(tool, str) for tool in turn.get("must_call", []))
        for criterion in turn.get("must_contain", []) + turn.get("must_not_contain", []):
            alternatives = criterion if isinstance(criterion, list) else [criterion]
            assert alternatives and all(isinstance(text, str) and text for text in alternatives)


@pytest.mark.parametrize("case", golden_cases(), ids=lambda case: case["id"])
def test_every_source_file_exists(case: dict) -> None:
    if "source" in case:
        assert (GOLDEN_PATH.parent.parent / case["source"]).is_file(), case["source"]
