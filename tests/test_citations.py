"""Formato único de data e de fonte nas respostas das ferramentas (T7.7, D53): o modelo só copia, não converte."""

import pytest

from case_assistant.citations import REGISTRY_SOURCE, brazilian_date, document_source, movement_source


@pytest.mark.parametrize(
    ("iso_date", "expected"),
    [("2025-11-17", "17/11/2025"), ("2022-02-02", "02/02/2022"), (None, None)],
    ids=["t7.4_wrong_date_case", "t7.2_iso_date_case", "missing"],
)
def test_brazilian_date(iso_date, expected) -> None:
    assert brazilian_date(iso_date) == expected


def test_movement_source_follows_the_format_in_the_instructions() -> None:
    assert movement_source(9219, "Sentença com Resolução do Mérito", "2026-02-18") == (
        "[mov. 9219 — Sentença com Resolução do Mérito, 18/02/2026]"
    )


def test_document_source_follows_the_format_in_the_instructions() -> None:
    assert document_source(7878, "Sentença", "2026-02-18") == "[doc 7878 — Sentença, 18/02/2026]"


def test_registry_source() -> None:
    assert REGISTRY_SOURCE == "[cadastro do processo]"
