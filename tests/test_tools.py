"""Ferramentas de consulta do agente, testadas sem IA sobre o banco real (somente leitura)."""

from contextlib import closing

import pytest

from case_assistant.db import connect
from case_assistant.tools import find_case

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"  # processo 3161: 19 documentos, juiz aposentado
CASE_WITHOUT_JUDGE_NUMBER = "0000001-63.2025.8.99.9059"  # processo 4: magistrado_id NULL
MISSING_CASE_NUMBER = "9999999-99.2099.8.99.9999"
LOWERCASE_STATUS_CASE_NUMBER = "0000001-43.2021.8.99.9014"  # processo 1: situacao "julgado"
UPPERCASE_STATUS_CASE_NUMBER = "0000002-98.2020.8.99.9002"  # situacao "JULGADO"
NORMALIZED_STATUSES = {"arquivado", "em andamento", "julgado", "suspenso"}


@pytest.fixture(scope="module")
def connection():
    with closing(connect()) as database_connection:
        yield database_connection


def test_find_case_returns_identification_card(connection) -> None:
    case = find_case(connection, REFERENCE_CASE_NUMBER)

    assert case == {
        "found": True,
        "case_number": REFERENCE_CASE_NUMBER,
        "case_class": "Procedimento Comum Cível",
        "subject": "Acidente de Trânsito",
        "district": "São Bento do Sul",
        "court_unit": "1ª Vara Cível",
        "court_unit_district": "São Bento do Sul",
        "judge": {"name": "Luiz Bonetti Vasconcelos", "status": "aposentado"},
        "filing_date": "2023-12-13",
        "sentence_date": "2026-02-18",
        "claim_value": 3796.73,
        "status": "julgado",
        "document_count": 19,
        "movement_count": 21,
    }


def test_find_case_accepts_number_inside_text_or_digits_only(connection) -> None:
    assert find_case(connection, f"processo {REFERENCE_CASE_NUMBER}")["case_number"] == REFERENCE_CASE_NUMBER
    assert find_case(connection, "00000077920238999014")["case_number"] == REFERENCE_CASE_NUMBER


def test_find_case_keeps_cases_without_judge(connection) -> None:
    case = find_case(connection, CASE_WITHOUT_JUDGE_NUMBER)

    assert case["found"] is True
    assert case["judge"] is None


def test_find_case_reports_missing_case_without_raising(connection) -> None:
    case = find_case(connection, MISSING_CASE_NUMBER)

    assert case == {"found": False, "message": f"Processo {MISSING_CASE_NUMBER} não encontrado no banco."}


def test_find_case_reports_text_without_case_number(connection) -> None:
    case = find_case(connection, "o processo do João")

    assert case["found"] is False
    assert "número de processo" in case["message"]


@pytest.mark.parametrize(
    "case_number",
    [LOWERCASE_STATUS_CASE_NUMBER, REFERENCE_CASE_NUMBER, UPPERCASE_STATUS_CASE_NUMBER],
    ids=["lowercase", "capitalized", "uppercase"],
)
def test_find_case_normalizes_status_casing(connection, case_number: str) -> None:
    assert find_case(connection, case_number)["status"] == "julgado"


def test_find_case_status_has_only_four_normalized_values(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]

    assert {find_case(connection, number)["status"] for number in numbers} == NORMALIZED_STATUSES
