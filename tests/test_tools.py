"""Ferramentas de consulta do agente, testadas sem IA sobre o banco real (somente leitura)."""

from contextlib import closing

import pytest

from case_assistant.db import connect
from case_assistant.tools import find_case, list_parties

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"  # processo 3161: 19 documentos, juiz aposentado
CASE_WITHOUT_JUDGE_NUMBER = "0000001-63.2025.8.99.9059"  # processo 4: magistrado_id NULL
MISSING_CASE_NUMBER = "9999999-99.2099.8.99.9999"
LOWERCASE_STATUS_CASE_NUMBER = "0000001-43.2021.8.99.9014"  # processo 1: situacao "julgado"
UPPERCASE_STATUS_CASE_NUMBER = "0000002-98.2020.8.99.9002"  # situacao "JULGADO"
DUPLICATED_PARTY_CASE_ID = 642  # "Anderson Cunha" vinculado duas vezes ao polo ativo
IMPLAUSIBLE_VALUE_CASE_ID = 6348  # valor da causa 9.999.999.999 — o seguinte no banco é 1,27 milhão
INACTIVE_UNIT_CASE_ID = 30  # vara "Vara da Fazenda Pública" de Joinville, desativada
CASE_WITHOUT_ANY_SENTENCE_SIGNAL_NUMBER = CASE_WITHOUT_JUDGE_NUMBER  # processo 4: nenhum dos três sinais
NORMALIZED_STATUSES = {"arquivado", "em andamento", "julgado", "suspenso"}


@pytest.fixture(scope="module")
def connection():
    with closing(connect()) as database_connection:
        yield database_connection


def test_find_case_returns_identification_card(connection) -> None:
    case = find_case(connection, REFERENCE_CASE_NUMBER)

    assert {field: value for field, value in case.items() if field not in {"judgment", "warnings"}} == {
        "found": True,
        "case_number": REFERENCE_CASE_NUMBER,
        "case_class": "Procedimento Comum Cível",
        "subject": "Acidente de Trânsito",
        "district": "São Bento do Sul",
        "court_unit": "1ª Vara Cível",
        "court_unit_district": "São Bento do Sul",
        "court_unit_status": "ativa",
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


def test_judgment_when_all_three_signals_agree(connection) -> None:
    judgment = find_case(connection, REFERENCE_CASE_NUMBER)["judgment"]

    assert judgment == {
        "summary": "Julgado: data de sentença, movimentação de sentença e documento de sentença conferem.",
        "sentence_movement": {"code": 9219, "description": "Sentença com Resolução do Mérito", "date": "2026-02-18"},
        "sentence_document": {"id": 7878, "type": "Sentença", "date": "2026-02-18"},
    }


def test_judgment_reports_sentence_date_without_sentence_text(connection) -> None:
    judgment = find_case(connection, LOWERCASE_STATUS_CASE_NUMBER)["judgment"]

    assert judgment["summary"] == (
        "Sinais divergentes. Presentes: data de sentença, movimentação de sentença. "
        "Ausente: documento de sentença (o texto da sentença não está no banco)."
    )
    assert judgment["sentence_document"] is None


def test_judgment_when_there_is_no_sentence_signal(connection) -> None:
    judgment = find_case(connection, CASE_WITHOUT_ANY_SENTENCE_SIGNAL_NUMBER)["judgment"]

    assert judgment["summary"].startswith("Não há sinal de sentença")
    assert judgment["sentence_movement"] is None


def test_judgment_counts_match_database_profile(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]
    summaries = [find_case(connection, number)["judgment"]["summary"] for number in numbers]

    assert sum(summary.startswith("Julgado") for summary in summaries) == 1_775
    assert sum(summary.startswith("Não há sinal") for summary in summaries) == 3_671
    assert sum(summary.startswith("Sinais divergentes") for summary in summaries) == 4_554
    # sem documento, mas com outro sinal: data+movimentação (4.413), só movimentação (83), só data (13)
    assert sum("não está no banco" in summary for summary in summaries) == 4_413 + 83 + 13


def warnings_for(connection, case_id: int) -> list[str]:
    case_number = connection.execute("SELECT numero FROM processo WHERE id = ?", (case_id,)).fetchone()["numero"]
    return find_case(connection, case_number)["warnings"]


def test_warnings_report_retired_judge(connection) -> None:
    assert find_case(connection, REFERENCE_CASE_NUMBER)["warnings"] == [
        "Magistrado Luiz Bonetti Vasconcelos está aposentado."
    ]


@pytest.mark.parametrize(
    ("case_id", "expected_warning"),
    [
        (4, "Processo sem magistrado cadastrado."),
        (3, "está removido."),
        (11, "A comarca está grafada de forma diferente no processo ('CRICIÚMA') e na vara ('Criciúma')."),
        (134, "grafada de forma diferente no processo ('S. José') e na vara ('São José')"),
        (2, "Valor da causa não informado."),
        (6, "Valor da causa inválido"),
        (IMPLAUSIBLE_VALUE_CASE_ID, "Valor da causa implausível (R$ 9.999.999.999,00)"),
        (17, "Situação 'julgado' sem data de sentença."),
        (INACTIVE_UNIT_CASE_ID, "está desativada."),
    ],
    ids=["missing_judge", "removed_judge", "district_casing", "district_abbreviation", "missing_value", "non_positive_value", "implausible_value", "judged_without_date", "inactive_unit"],
)
def test_warnings_report_registry_inconsistencies(connection, case_id: int, expected_warning: str) -> None:
    assert any(expected_warning in warning for warning in warnings_for(connection, case_id))


def test_warnings_counts_match_database_profile(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]
    all_warnings = [warning for number in numbers for warning in find_case(connection, number)["warnings"]]

    def count(fragment: str) -> int:
        return sum(fragment in warning for warning in all_warnings)

    assert count("sem magistrado") == 1_044
    assert count("está aposentado") + count("está removido") == 2_022
    # as 1.024 diferenças de comarca do banco são a mesma cidade escrita de outro jeito; nenhuma é outra cidade
    assert count("grafada de forma diferente") == 1_024
    assert count("difere da comarca da vara") == 0
    assert count("Valor da causa") == 886 + 1  # 598 vazios + 288 <= 0 + 1 implausível
    assert count("sem data de sentença") == 43
    assert count("está desativada") == 746


def case_number_of(connection, case_id: int) -> str:
    return connection.execute("SELECT numero FROM processo WHERE id = ?", (case_id,)).fetchone()["numero"]


def test_list_parties_groups_by_pole(connection) -> None:
    assert list_parties(connection, REFERENCE_CASE_NUMBER) == {
        "found": True,
        "case_number": REFERENCE_CASE_NUMBER,
        "plaintiffs": [{"name": "João Ziegler Rocha", "person_type": "pessoa física", "document": "999.539.988-87"}],
        "defendants": [
            {"name": "Operadora de Saúde Cambirela Ltda", "person_type": "pessoa jurídica", "document": "99.193.997/0001-35"}
        ],
        "warnings": [],
    }


def test_list_parties_shows_duplicated_link_once_and_warns(connection) -> None:
    parties = list_parties(connection, case_number_of(connection, DUPLICATED_PARTY_CASE_ID))

    assert [party["name"] for party in parties["plaintiffs"]].count("Anderson Cunha") == 1
    assert parties["warnings"] == ["Anderson Cunha aparece mais de uma vez no polo ativo do cadastro."]


def test_list_parties_reports_missing_case(connection) -> None:
    assert list_parties(connection, MISSING_CASE_NUMBER) == {
        "found": False,
        "message": f"Processo {MISSING_CASE_NUMBER} não encontrado no banco.",
    }


def test_list_parties_covers_every_case(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]
    all_parties = [list_parties(connection, number) for number in numbers]

    assert all(parties["plaintiffs"] and parties["defendants"] for parties in all_parties)
    assert sum(len(parties["plaintiffs"]) + len(parties["defendants"]) for parties in all_parties) == 25_086 - 99
    assert sum(len(parties["warnings"]) for parties in all_parties) == 99
