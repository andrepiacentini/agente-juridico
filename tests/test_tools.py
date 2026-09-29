"""Ferramentas de consulta do agente, testadas sem IA sobre o banco real (somente leitura)."""

import re
from contextlib import closing

import sqlite3

import pytest

from case_assistant.db import connect, create_search_index
from case_assistant.tools import check_draft_basis, find_case, prepare_draft, list_documents, list_movements, list_parties, read_document, search_cases, search_parties, search_text

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"  # processo 3161: 19 documentos, juiz aposentado
CASE_WITHOUT_JUDGE_NUMBER = "0000001-63.2025.8.99.9059"  # processo 4: magistrado_id NULL
SENTENCE_DOCUMENT_WITHOUT_DATE_CASE_NUMBER = "0000001-61.2021.8.99.9008"
MISSING_CASE_NUMBER = "0000999-40.2023.8.99.9014"  # dígito verificador certo, mas fora do banco
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
        "filing_date": "13/12/2023",
        "sentence_date": "18/02/2026",
        "claim_value": 3796.73,
        "status": "julgado",
        "document_count": 19,
        "movement_count": 21,
        "source": "[cadastro do processo]",
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


def test_find_case_warns_about_a_likely_typo_when_the_check_digits_fail(connection) -> None:
    # O 3161 com o dígito verificador trocado (79 → 78): em vez de só "não existe", o provável erro de digitação.
    case = find_case(connection, "0000007-78.2023.8.99.9014")

    assert case == {
        "found": False,
        "message": "Processo 0000007-78.2023.8.99.9014 não encontrado no banco. O dígito verificador (78) não confere "
        "com o restante do número: provavelmente houve erro de digitação. Confira o número do processo.",
    }


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
        # D66: sem dizer onde está o texto, o modelo local respondeu que ele "não está disponível no banco".
        "summary": "Julgado: data de sentença, movimentação de sentença e documento de sentença conferem. "
        "O texto da sentença, com a decisão e os fundamentos, está no [doc 7878 — Sentença, 18/02/2026].",
        "sentence_movement": {
            "code": 9219, "description": "Sentença com Resolução do Mérito", "date": "18/02/2026",
            "source": "[mov. 9219 — Sentença com Resolução do Mérito, 18/02/2026]",
        },
        "sentence_document": {
            "id": 7878, "type": "Sentença", "date": "18/02/2026", "source": "[doc 7878 — Sentença, 18/02/2026]",
        },
    }


def test_judgment_reports_sentence_date_without_sentence_text(connection) -> None:
    judgment = find_case(connection, LOWERCASE_STATUS_CASE_NUMBER)["judgment"]

    assert judgment["summary"] == (
        "Sinais divergentes. Presentes: data de sentença, movimentação de sentença. "
        "Ausente: documento de sentença (o texto da sentença não está no banco)."
    )
    assert judgment["sentence_document"] is None


def test_judgment_points_to_the_sentence_text_even_without_sentence_date(connection) -> None:
    judgment = find_case(connection, SENTENCE_DOCUMENT_WITHOUT_DATE_CASE_NUMBER)["judgment"]

    assert judgment["summary"].startswith("Sinais divergentes.")
    assert judgment["summary"].endswith(
        "O texto da sentença, com a decisão e os fundamentos, está no [doc 922 — Sentença, 17/02/2023]."
    )


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
    # com documento de sentença: os 1.775 julgados e os 45 divergentes que têm o documento
    assert sum("O texto da sentença, com a decisão e os fundamentos, está no [doc" in summary for summary in summaries) == 1_775 + 45


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
        (6, "Valor da causa inválido (R$ 0,00)."),
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
        "source": "[cadastro do processo]",
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
    # Cada movimentação é só a citação pronta: ela já traz código, descrição e data, e custa menos contexto (D53).
    assert movements[0] == "[mov. 9926 — Distribuição por Sorteio, 11/01/2021]"
    assert movements[10] == "[mov. 9219 — Sentença com Resolução do Mérito, 02/02/2022]"
    as_iso = ["-".join(reversed(re.search(r"(\d{2}/\d{2}/\d{4})\]$", movement).group(1).split("/"))) for movement in movements]
    assert as_iso == sorted(as_iso)


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
        "Recurso de apelação registrado em 04/03/2022, depois do trânsito em julgado (21/02/2022). "
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
        "date": "08/01/2024",
        "pages": 2,
        "lawyer_side": "autor",
        "source": "[doc 7865 — Petição Inicial, 08/01/2024]",
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
        "date": "18/02/2026",
        "pages": 2,
        "source": "[doc 7878 — Sentença, 18/02/2026]",
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


@pytest.fixture(scope="module")
def indexed_connection():
    with closing(connect()) as database_connection:
        create_search_index(database_connection)
        yield database_connection


def test_search_text_finds_documents_with_snippet(indexed_connection) -> None:
    result = search_text(indexed_connection, "inversão do ônus")

    assert result["found"] is True
    assert result["match"] == "frase exata"
    assert result["total"] == 2_786
    assert len(result["results"]) == 10
    first = result["results"][0]
    assert set(first) == {"document_id", "case_number", "type", "date", "snippet", "source"}
    assert first["source"] == f"[doc {first['document_id']} — {first['type']}, {first['date']}]"
    assert "[inversão do ônus]" in first["snippet"].lower()


def test_search_text_ignores_accents(indexed_connection) -> None:
    assert search_text(indexed_connection, "inversao do onus")["total"] == 2_786


def test_search_text_filters_by_case_and_type(indexed_connection) -> None:
    in_case = search_text(indexed_connection, "trânsito", case_number=REFERENCE_CASE_NUMBER)
    sentences = search_text(indexed_connection, "dano moral", document_type="sentença")

    # ordenados por relevância; aqui importa o conjunto
    assert {result["document_id"] for result in in_case["results"]} == {7865, 7878, 7881}
    assert sentences["total"] == 128
    assert {result["type"] for result in sentences["results"]} == {"Sentença"}


def test_search_text_falls_back_to_all_words_when_phrase_is_absent(indexed_connection) -> None:
    result = search_text(indexed_connection, "prova ônus")

    assert result["match"] == "todas as palavras"
    assert result["total"] == 3_778


@pytest.mark.parametrize("term", ["boa-fé", "art. 373", 'ônus "da', "AND", "NEAR(x)"])
def test_search_text_is_safe_with_special_characters(indexed_connection, term: str) -> None:
    assert search_text(indexed_connection, term)["found"] in {True, False}


def test_search_text_without_matches_says_so(indexed_connection) -> None:
    result = search_text(indexed_connection, "xyzabc inexistente")

    assert result == {"found": False, "message": "Nenhum documento menciona 'xyzabc inexistente'."}


def test_search_text_respects_limit(indexed_connection) -> None:
    result = search_text(indexed_connection, "ônus da prova", limit=100)

    assert len(result["results"]) == 20
    assert result["total"] == 1_871


def test_search_text_reports_missing_case_filter(indexed_connection) -> None:
    assert search_text(indexed_connection, "ônus", case_number=MISSING_CASE_NUMBER)["found"] is False


def test_search_parties_finds_person_with_cases_and_pole(indexed_connection) -> None:
    result = search_parties(indexed_connection, "João Ziegler Rocha")

    assert result["found"] is True
    assert result["total_people"] == 1
    assert "homonym_notice" not in result
    person = result["people"][0]
    assert person["document"] == "999.539.988-87"
    assert person["person_type"] == "pessoa física"
    assert person["names"] == ["João Ziegler Rocha"]
    # O papel no processo sai como autor/réu: "polo ativo" virou "processo ativo" na resposta do modelo (D50).
    assert {"case_number": REFERENCE_CASE_NUMBER, "role": "autor"} in person["cases"]


def test_search_parties_ignores_accents_and_word_order(indexed_connection) -> None:
    result = search_parties(indexed_connection, "rocha joao")

    assert "999.539.988-87" in {person["document"] for person in result["people"]}


def test_search_parties_separates_homonyms_and_asks_which_one(indexed_connection) -> None:
    result = search_parties(indexed_connection, "Ademir Fabris")

    assert result["total_people"] == 2
    assert [person["case_count"] for person in result["people"]] == [2, 1]  # quem tem mais processos primeiro
    # O modelo pequeno repassa o aviso ao pé da letra (D50): o texto tem que servir ao usuário e terminar na pergunta.
    assert result["homonym_notice"] == (
        "Encontrei 2 pessoas diferentes com esse nome (CPF/CNPJ distintos). De qual delas se trata?"
    )


def test_search_parties_warns_when_same_document_has_different_names(indexed_connection) -> None:
    result = search_parties(indexed_connection, "Imobiliária Mendes")
    person = next(person for person in result["people"] if person["document"] == "99.015.411/0001-85")

    assert person["names"] == ["Imobiliária Mendes Ltda", "Imobiliária Mendez Ltda"]
    assert person["case_count"] == 1  # as duas linhas do cadastro estão no mesmo processo
    assert (
        "O documento 99.015.411/0001-85 aparece no cadastro com nomes diferentes: "
        "Imobiliária Mendes Ltda, Imobiliária Mendez Ltda."
    ) in result["warnings"]


def test_search_parties_caps_people_and_cases(indexed_connection) -> None:
    result = search_parties(indexed_connection, "Maria")

    assert len(result["people"]) == 10
    assert result["total_people"] > 10
    assert all(len(person["cases"]) <= 10 for person in result["people"])


def test_search_parties_without_matches_says_so(indexed_connection) -> None:
    assert search_parties(indexed_connection, "Xyzabc Inexistente") == {
        "found": False,
        "message": "Nenhuma parte com o nome 'Xyzabc Inexistente'.",
    }


def test_search_parties_flags_every_homonym_in_database(indexed_connection) -> None:
    homonym_names = [
        row["nome"]
        for row in indexed_connection.execute(
            "SELECT nome FROM parte GROUP BY nome HAVING COUNT(DISTINCT documento) > 1"
        )
    ]

    assert len(homonym_names) == 643
    assert all("homonym_notice" in search_parties(indexed_connection, name) for name in homonym_names)


def case_numbers(result) -> set[str]:
    return {case["case_number"] for case in result["cases"]}


def test_search_cases_by_subject_ignores_accents_and_case(connection) -> None:
    result = search_cases(connection, subject="plano de saude")

    assert result["total"] == 444
    assert len(result["cases"]) == 20
    assert set(result["cases"][0]) == {
        "case_number", "case_class", "subject", "district", "status", "filing_date", "claim_value"
    }
    assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", result["cases"][0]["filing_date"])


def test_search_cases_combines_class_and_district(connection) -> None:
    assert search_cases(connection, case_class="execução fiscal", district="joinville")["total"] == 127


def test_search_cases_by_judge(connection) -> None:
    result = search_cases(connection, judge="Luiz Bonetti Vasconcelos", limit=50)

    assert result["total"] == 23
    assert REFERENCE_CASE_NUMBER in case_numbers(result)


def test_search_cases_by_status_and_filing_period(connection) -> None:
    result = search_cases(connection, status="Em Andamento", filing_date_from="2024-01-01", filing_date_to="2024-12-31")

    assert result["total"] == 389
    assert {case["status"] for case in result["cases"]} == {"em andamento"}


def test_search_cases_orders_by_claim_value(connection) -> None:
    result = search_cases(connection, claim_value_min=1_000_000, order_by="claim_value", limit=3)

    assert [case["claim_value"] for case in result["cases"]] == [9_999_999_999.0, 1_267_818.19, 1_217_252.87]


def test_search_cases_limit_keeps_total(connection) -> None:
    result = search_cases(connection, subject="plano de saude", limit=500)

    assert len(result["cases"]) == 50
    assert result["total"] == 444


def test_search_cases_requires_at_least_one_filter(connection) -> None:
    result = search_cases(connection)

    assert result["found"] is False
    assert "ao menos um filtro" in result["message"]


def test_search_cases_rejects_invalid_date_and_order(connection) -> None:
    assert "data" in search_cases(connection, filing_date_from="13/2024")["message"]
    assert "ordenação" in search_cases(connection, subject="saúde", order_by="nome")["message"].lower()


def test_search_cases_without_matches_says_so(connection) -> None:
    # Cada filtro sozinho encontra processos; só a combinação não (nenhum divórcio corre em vara da Fazenda).
    assert search_cases(connection, case_class="divórcio", court_unit="fazenda") == {
        "found": False,
        "message": "Nenhum processo atende a todos os filtros juntos; cada um, sozinho, encontra processos.",
    }


def test_search_cases_names_a_class_that_does_not_exist_and_lists_the_real_ones(connection) -> None:
    # D52: com "Nenhum processo atende aos filtros", o modelo concluiu, falsamente, que não havia processo com valor.
    result = search_cases(connection, case_class="any", claim_value_max=9_999_999_999)
    classes = [row["classe"] for row in connection.execute("SELECT DISTINCT classe FROM processo ORDER BY classe")]

    assert result == {
        "found": False,
        "message": f"Não há classe com 'any' no banco. Classes que existem: {', '.join(classes)}.",
    }


@pytest.mark.parametrize(
    ("filters", "expected_start"),
    [
        ({"subject": "assunto inexistente xyz"}, "Não há assunto com 'assunto inexistente xyz' no banco. Assuntos que existem: "),
        ({"court_unit": "vara espacial"}, "Não há vara com 'vara espacial' no banco. Varas que existem: "),
        ({"status": "pendente"}, "Não há situação com 'pendente' no banco. Situações que existem: arquivado, em andamento, julgado, suspenso."),
    ],
    ids=["subject", "court_unit", "status"],
)
def test_search_cases_lists_the_real_values_of_short_lists(connection, filters, expected_start: str) -> None:
    assert search_cases(connection, **filters)["message"].startswith(expected_start)


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        ({"district": "Atlântida"}, "Não há comarca com 'Atlântida' no banco."),
        ({"judge": "Fulano Inexistente"}, "Não há magistrado com 'Fulano Inexistente' no banco."),
    ],
    ids=["district", "judge"],
)
def test_search_cases_does_not_list_long_lists(connection, filters, expected: str) -> None:
    # 230 comarcas e 200 magistrados: a lista custaria contexto demais para o modelo local.
    assert search_cases(connection, **filters)["message"] == expected


INITIAL_PETITION_ONLY_CASE_NUMBER = "0000001-02.2025.8.99.9047"


def test_draft_basis_is_ready_with_initial_petition_and_defense(connection) -> None:
    assert check_draft_basis(connection, REFERENCE_CASE_NUMBER) == {
        "found": True,
        "case_number": REFERENCE_CASE_NUMBER,
        "ready": True,
        "missing": [],
    }


def test_draft_basis_lists_both_documents_missing_in_a_case_without_documents(connection) -> None:
    result = check_draft_basis(connection, LOWERCASE_STATUS_CASE_NUMBER)

    assert result["ready"] is False
    assert result["missing"] == ["Petição Inicial", "Contestação"]


def test_draft_basis_lists_only_the_missing_defense(connection) -> None:
    assert check_draft_basis(connection, INITIAL_PETITION_ONLY_CASE_NUMBER)["missing"] == ["Contestação"]


def test_draft_basis_reports_missing_case(connection) -> None:
    assert check_draft_basis(connection, MISSING_CASE_NUMBER)["found"] is False


def test_draft_basis_counts_match_database_profile(connection) -> None:
    numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]
    results = [check_draft_basis(connection, number) for number in numbers]

    # 1.586 com as duas peças; 2.105 só com a petição inicial; nenhum só com a contestação
    assert sum(result["ready"] for result in results) == 1_586
    assert sum(result["missing"] == ["Contestação"] for result in results) == 2_105
    assert sum(result["missing"] == ["Petição Inicial"] for result in results) == 0


def test_prepare_draft_lists_the_documents_to_read_and_points_to_the_existing_sentence(connection) -> None:
    result = prepare_draft(connection, REFERENCE_CASE_NUMBER)

    assert result["ready"] is True
    assert [(document["id"], document["type"]) for document in result["documents_to_read"]] == [
        (7865, "Petição Inicial"),
        (7868, "Contestação"),
        (7869, "Réplica"),
        (7870, "Decisão de Saneamento"),
        (7875, "Ata de Audiência"),
    ]
    assert result["documents_to_read"][0]["source"] == "[doc 7865 — Petição Inicial, 08/01/2024]"
    # A sentença que já existe fica fora da leitura: a minuta é proposta independente, não cópia (D57).
    assert result["existing_sentences"] == ["[doc 7878 — Sentença, 18/02/2026]"]


def test_prepare_draft_without_basis_says_what_is_missing_in_words_for_the_user(connection) -> None:
    result = prepare_draft(connection, LOWERCASE_STATUS_CASE_NUMBER)

    assert result == {
        "found": True,
        "case_number": LOWERCASE_STATUS_CASE_NUMBER,
        "ready": False,
        "missing": ["Petição Inicial", "Contestação"],
        "message": "Não é possível propor uma minuta de sentença para o processo "
        f"{LOWERCASE_STATUS_CASE_NUMBER}: faltam no banco a petição inicial e a contestação. "
        "Sem elas, não há o pedido do autor nem a defesa do réu.",
    }


def test_prepare_draft_names_a_single_missing_document(connection) -> None:
    message = prepare_draft(connection, INITIAL_PETITION_ONLY_CASE_NUMBER)["message"]

    assert message.endswith("falta no banco a contestação. Sem ela, não há a defesa do réu.")


def test_prepare_draft_reports_missing_case(connection) -> None:
    assert prepare_draft(connection, MISSING_CASE_NUMBER)["found"] is False
