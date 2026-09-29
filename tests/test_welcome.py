"""Tela de boas-vindas do chat web (T10.4, D70): as 4 perguntas do edital, prontas para clicar. Sem IA."""

from pathlib import Path

import yaml

import app

GOLDEN_PATH = Path(__file__).parent / "golden.yaml"
EDITAL_CASES_FOR_3161 = ("edital-1-resumo-3161", "edital-2-partes-3161", "edital-3-julgamento-3161", "edital-4-minuta-3161")


def test_welcome_shows_the_four_edital_questions_as_they_are_in_the_battery() -> None:
    # O mesmo texto da bateria: o que a banca clica é exatamente o que foi medido (D65).
    cases = {case["id"]: case for case in yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8"))["cases"]}
    battery_questions = [cases[case_id]["turns"][0]["ask"] for case_id in EDITAL_CASES_FOR_3161]

    assert [starter.message for starter in app.WELCOME_STARTERS] == battery_questions


def test_every_welcome_button_has_a_short_label() -> None:
    assert all(0 < len(starter.label) <= 30 for starter in app.WELCOME_STARTERS)
