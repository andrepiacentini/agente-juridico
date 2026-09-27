"""Ferramentas de consulta do agente, testadas sem IA sobre o banco real (somente leitura)."""

from contextlib import closing

import sqlite3

import pytest

from case_assistant.db import connect
from case_assistant.tools import find_case, list_documents, list_movements, list_parties, read_document

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"  # processo 3161: 19 documentos, juiz aposentado
CASE_WITHOUT_JUDGE_NUMBER = "0000001-63.2025.8.99.9059"  # processo 4: magistrado_id NULL
MISSING_CASE_NUMBER = "9999999-99.2099.8.99.9999"
LOWERCASE_STATUS_CASE_NUMBER = "0000001-43.2021.8.99.9014"  # processo 1: situacao "julgado"
UPPERCASE_STATUS_CASE_NUMBER = "0000002-98.2020.8.99.9002"  # situacao "JULGADO"
DUPLICATED_PARTY_CASE_ID = 642  # "Anderson Cunha" vinculado duas vezes ao polo ativo
IMPLAUSIBLE_VALUE_CASE_ID = 6348  # valor da causa 9.999.999.999 — o seguinte no banco é 1,27 milhão
CASE_WITHOUT_MOVEMENTS_NUMBER = "0000013-87.2026.8.99.9012"  # processo 3611
SIGNATURE_MISMATCH_CASE_NUMBER = "0000001-46.2021.8.99.9013"  # processo 180: doc 543 assinado por outra OAB
LAWYER_ON_BOTH_SIDES_CASE_NUMBER = "0000002-07.2025.8.99.9008"  # processo 884: mesma OAB na inicial e na contestação
REFERENCE_SENTENCE_ID = 7878  # sentença do processo 3161, 2.443 caracteres
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


def test_list_movements_returns_timeline_in_date_order(connection) -> None:
    result = list_movements(connection, LOWERCASE_STATUS_CASE_NUMBER)
    movements = result["movements"]

    assert result["found"] is True
    assert len(movements) == 16
    assert movements[0] == {"date": "2021-01-11", "code": 9926, "description": "Distribuição por Sorteio"}
    assert movements[10] == {"date": "2022-02-02", "code": 9219, "description": "Sentença com Resolução do Mérito"}
    assert [movement["date"] for movement in movements] == sorted(movement["date"] for movement in movements)


def test_list_movements_of_case_without_movements_is_empty(connection) -> None:
    result = list_movements(connection, CASE_WITHOUT_MOVEMENTS_NUMBER)

    assert result["found"] is True
    assert result["movements"] == []


def test_list_movements_reports_missing_case(connection) -> None:
    assert list_movements(connection, MISSING_CASE_NUMBER)["found"] is False


def test_list_movements_covers_every_linked_movement(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]
    total = sum(len(list_movements(connection, number)["movements"]) for number in numbers)

    # 134.046 no banco menos as 402 movimentações órfãs, que não pertencem a nenhum processo
    assert total == 134_046 - 402


def test_list_movements_warns_about_appeal_after_final_judgment(connection) -> None:
    warnings = list_movements(connection, LOWERCASE_STATUS_CASE_NUMBER)["warnings"]

    assert warnings == [
        "Recurso de apelação registrado em 2022-03-04, depois do trânsito em julgado (2022-02-21). "
        "Sequência incomum, que merece conferência: pode ser recurso interposto fora do prazo ou erro de cadastro."
    ]


def test_list_movements_without_contradictions_has_no_warnings(connection) -> None:
    assert list_movements(connection, REFERENCE_CASE_NUMBER)["warnings"] == []


def test_list_movements_warning_counts_match_database_profile(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]
    warnings_per_case = [list_movements(connection, number)["warnings"] for number in numbers]

    assert sum(any("depois do trânsito em julgado" in w for w in warnings) for warnings in warnings_per_case) == 220
    # 32 se contadas também as movimentações órfãs (sem processo); só processos existentes, 16
    assert sum(any("sem movimentação de sentença" in w for w in warnings) for warnings in warnings_per_case) == 16


def test_list_documents_returns_metadata_without_text(connection) -> None:
    result = list_documents(connection, REFERENCE_CASE_NUMBER)
    documents = result["documents"]

    assert len(documents) == 19
    assert documents[0] == {
        "id": 7865,
        "type": "Petição Inicial",
        "author": "Dr. Carlos Gava Reis — OAB/SC 99.170",
        "date": "2024-01-08",
        "pages": 2,
        "lawyer_side": "autor",
    }
    assert documents[1]["lawyer_side"] is None  # despacho do juiz
    assert all("text" not in document and "texto" not in document for document in documents)


def test_list_documents_identifies_each_lawyer_and_side(connection) -> None:
    lawyers = list_documents(connection, REFERENCE_CASE_NUMBER)["lawyers"]

    assert lawyers == [
        {
            "name": "Dr. Carlos Gava Reis",
            "oab": "OAB/SC 99.170",
            "side": "autor",
            "document_ids": [7865, 7869, 7872, 7873, 7877, 7879, 7881],
        },
        {"name": "Dra. Sônia Weber Azevedo", "oab": "OAB/SC 99.854", "side": "réu", "document_ids": [7868, 7882]},
    ]


def test_list_documents_of_case_without_documents_is_empty(connection) -> None:
    result = list_documents(connection, LOWERCASE_STATUS_CASE_NUMBER)

    assert result["found"] is True
    assert result["documents"] == [] and result["lawyers"] == [] and result["warnings"] == []


def test_list_documents_warns_when_signature_differs_from_author(connection) -> None:
    warnings = list_documents(connection, SIGNATURE_MISMATCH_CASE_NUMBER)["warnings"]

    assert (
        "Documento 543: o autor cadastrado (Dra. Sandra Valente Lopes — OAB/SC 99.438) "
        "difere da assinatura no texto (OAB/SC 99.790)."
    ) in warnings


def test_list_documents_warns_about_lawyer_on_both_sides(connection) -> None:
    result = list_documents(connection, LAWYER_ON_BOTH_SIDES_CASE_NUMBER)

    assert any(lawyer["side"] == "ambos os lados" for lawyer in result["lawyers"])
    assert any("assina peças dos dois lados" in warning for warning in result["warnings"])


def test_list_documents_counts_match_database_profile(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]
    results = [list_documents(connection, number) for number in numbers]
    warnings = [warning for result in results for warning in result["warnings"]]

    assert sum(len(result["documents"]) for result in results) == 25_582
    assert sum(not result["documents"] for result in results) == 6_309
    assert sum("difere da assinatura no texto" in warning for warning in warnings) == 309
    assert sum("assina peças dos dois lados" in warning for warning in warnings) == 8
    assert not any("O texto cita o processo" in warning for warning in warnings)


def test_read_document_returns_full_text_with_citation_data(connection) -> None:
    document = read_document(connection, REFERENCE_SENTENCE_ID)
    stored_text = connection.execute("SELECT texto FROM documento WHERE id = ?", (REFERENCE_SENTENCE_ID,)).fetchone()["texto"]

    assert {field: value for field, value in document.items() if field not in {"text", "warnings"}} == {
        "found": True,
        "id": REFERENCE_SENTENCE_ID,
        "case_number": REFERENCE_CASE_NUMBER,
        "type": "Sentença",
        "author": "Luiz Bonetti Vasconcelos",
        "date": "2026-02-18",
        "pages": 2,
    }
    assert document["text"] == stored_text
    assert len(document["text"]) == 2_443


def test_read_document_reports_missing_document(connection) -> None:
    assert read_document(connection, 999_999) == {
        "found": False,
        "message": "Documento 999999 não encontrado no banco.",
    }


@pytest.fixture
def in_memory_copy(connection):
    """Cópia do banco na memória, para simular dados que o banco real não tem; o arquivo nunca é alterado."""
    copy = sqlite3.connect(":memory:")
    connection.backup(copy)
    copy.row_factory = sqlite3.Row
    yield copy
    copy.close()


def test_read_document_has_no_warning_when_cited_number_matches(connection) -> None:
    assert read_document(connection, REFERENCE_SENTENCE_ID)["warnings"] == []


def test_read_document_warns_when_text_cites_another_case_number(in_memory_copy) -> None:
    in_memory_copy.execute(
        "UPDATE documento SET texto = replace(texto, ?, ?) WHERE id = ?",
        (REFERENCE_CASE_NUMBER, CASE_WITHOUT_JUDGE_NUMBER, REFERENCE_SENTENCE_ID),
    )

    warnings = read_document(in_memory_copy, REFERENCE_SENTENCE_ID)["warnings"]

    assert warnings == [
        f"O texto cita o processo {CASE_WITHOUT_JUDGE_NUMBER}, mas o documento pertence ao processo "
        f"{REFERENCE_CASE_NUMBER}. Merece conferência: pode ser documento juntado no processo errado."
    ]


def test_no_document_in_database_cites_another_case_number(connection) -> None:
    document_ids = [row["id"] for row in connection.execute("SELECT id FROM documento")]

    assert not any(read_document(connection, document_id)["warnings"] for document_id in document_ids)


def test_list_documents_warns_when_a_text_cites_another_case_number(in_memory_copy) -> None:
    in_memory_copy.execute(
        "UPDATE documento SET texto = replace(texto, ?, ?) WHERE id = ?",
        (REFERENCE_CASE_NUMBER, CASE_WITHOUT_JUDGE_NUMBER, REFERENCE_SENTENCE_ID),
    )

    warnings = list_documents(in_memory_copy, REFERENCE_CASE_NUMBER)["warnings"]

    assert (
        f"Documento {REFERENCE_SENTENCE_ID}: o texto cita o processo {CASE_WITHOUT_JUDGE_NUMBER}, mas o documento "
        f"pertence ao processo {REFERENCE_CASE_NUMBER}. Merece conferência: pode ser documento juntado no processo errado."
    ) in warnings


def test_reference_case_has_two_signature_divergences(connection) -> None:
    # manifestações cadastradas como do advogado do autor, mas assinadas com a OAB da advogada do réu
    assert list_documents(connection, REFERENCE_CASE_NUMBER)["warnings"] == [
        "Documento 7872: o autor cadastrado (Dr. Carlos Gava Reis — OAB/SC 99.170) "
        "difere da assinatura no texto (OAB/SC 99.854).",
        "Documento 7877: o autor cadastrado (Dr. Carlos Gava Reis — OAB/SC 99.170) "
        "difere da assinatura no texto (OAB/SC 99.854).",
    ]
