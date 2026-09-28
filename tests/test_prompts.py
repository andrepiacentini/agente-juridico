"""Descrição do banco para o modelo: completa, curta e com exemplos que de fato rodam."""

import re
from contextlib import closing

import pytest

from case_assistant.db import connect
from case_assistant import sql_query, tools
from case_assistant.citations import REGISTRY_SOURCE, document_source, movement_source
from case_assistant.prompts import DATABASE_DESCRIPTION, DRAFT_INSTRUCTIONS, DRAFT_NOTICE, SYSTEM_PROMPT
from case_assistant.sql_query import run_sql

# Estimativa conservadora para português: ~3,5 caracteres por token.
MAX_CHARACTERS_FOR_800_TOKENS = 2_800
MAX_CHARACTERS_FOR_1500_TOKENS = 5_250
AGENT_TOOLS = (
    "find_case", "list_parties", "list_movements", "list_documents", "read_document",
    "search_text", "search_parties", "search_cases", "run_sql", "prepare_draft",
)


@pytest.fixture(scope="module")
def connection():
    with closing(connect()) as database_connection:
        yield database_connection


def test_description_mentions_every_table_and_column(connection) -> None:
    tables = [
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
    ]
    for table in tables:
        columns = [column[1] for column in connection.execute(f"PRAGMA table_info({table})")]
        table_line = next(line for line in DATABASE_DESCRIPTION.splitlines() if line.startswith(f"- {table}("))
        assert all(re.search(rf"\b{column}\b", table_line) for column in columns), table


def test_description_fits_in_about_800_tokens() -> None:
    assert len(DATABASE_DESCRIPTION) <= MAX_CHARACTERS_FOR_800_TOKENS


@pytest.mark.parametrize(
    "trap",
    [
        "LOWER(TRIM(situacao))",
        "LEFT JOIN magistrado",
        "9219, 9220, 9221",
        "Sentença Homologatória de Acordo",
        "comparable_district",
        "polo",
        "OAB",
        "AAAA-MM-DD",
        "JOIN processo",
    ],
)
def test_description_warns_about_known_traps(trap: str) -> None:
    assert trap in DATABASE_DESCRIPTION


def test_example_queries_in_the_description_really_run(connection) -> None:
    examples = re.findall(r"^Exemplo: (SELECT .+)$", DATABASE_DESCRIPTION, flags=re.MULTILINE)

    assert len(examples) >= 2
    for example in examples:
        result = run_sql(connection, example)
        assert result["found"] is True, (example, result)


def test_system_prompt_includes_the_database_description() -> None:
    assert DATABASE_DESCRIPTION in SYSTEM_PROMPT


def test_system_prompt_fits_in_about_1500_tokens() -> None:
    assert len(SYSTEM_PROMPT) <= MAX_CHARACTERS_FOR_1500_TOKENS


def test_every_tool_mentioned_exists_in_the_code() -> None:
    mentioned = set(re.findall(r"\b([a-z]+_[a-z_]+)\(\)", SYSTEM_PROMPT))

    assert mentioned == set(AGENT_TOOLS)
    assert all(hasattr(tools, name) or hasattr(sql_query, name) for name in mentioned)


@pytest.mark.parametrize(
    "rule",
    [
        "português",
        "[doc 7878 — Sentença, 18/02/2026]",
        "[mov. 9219 — Sentença com Resolução do Mérito, 18/02/2026]",
        "Não consta",
        "homonym_notice",
        "warnings",
    ],
)
def test_system_prompt_has_the_core_rules(rule: str) -> None:
    assert rule in SYSTEM_PROMPT


def test_system_prompt_has_a_summary_playbook_in_tool_order() -> None:
    playbook = SYSTEM_PROMPT[SYSTEM_PROMPT.index("Para resumir um processo"):]
    steps = ["find_case()", "list_movements()", "list_documents()", "read_document()"]

    positions = [playbook.index(step) for step in steps]
    assert positions == sorted(positions)
    assert "petição inicial" in playbook and "sentença" in playbook
    assert "sem documentos" in playbook  # 63% dos processos: resumir pelo andamento


def test_system_prompt_forbids_deducing_facts_from_subject() -> None:
    assert "Não deduza fatos do assunto ou da classe do processo" in SYSTEM_PROMPT


def test_citation_examples_in_the_prompt_are_the_ones_the_tools_produce() -> None:
    # Um formato só (D53): o exemplo que o modelo lê é exatamente o que as ferramentas devolvem no campo source.
    assert document_source(7878, "Sentença", "2026-02-18") in SYSTEM_PROMPT
    assert movement_source(9219, "Sentença com Resolução do Mérito", "2026-02-18") in SYSTEM_PROMPT
    assert REGISTRY_SOURCE in SYSTEM_PROMPT


@pytest.mark.parametrize(
    "rule",
    [
        "source",  # copiar a citação pronta
        "já estiver na conversa",  # T5.5: dado do histórico também é citado
        "não crie avisos",  # T7.4: aviso inventado
        "nomes de campos",  # T7.2/T7.3: "Warning:", "o campo 'judge'"
        "autor ou réu",  # T7.4: polo lido como situação do processo
    ],
)
def test_system_prompt_has_the_citation_and_form_rules(rule: str) -> None:
    assert rule in SYSTEM_PROMPT


def test_draft_notice_is_the_one_the_edital_requires() -> None:
    assert DRAFT_NOTICE == "PROPOSTA DE MINUTA — texto não proferido"


@pytest.mark.parametrize(
    "rule",
    [DRAFT_NOTICE, "RELATÓRIO", "FUNDAMENTAÇÃO", "DISPOSITIVO", "read_document()", "jurisprudência", "[doc"],
)
def test_draft_instructions_have_the_structure_and_the_writing_rules(rule: str) -> None:
    assert rule in DRAFT_INSTRUCTIONS


def test_draft_instructions_stay_out_of_the_fixed_prompt() -> None:
    # Só chegam ao modelo quando ele pede uma minuta (D57): o prompt fixo vai em todo pedido.
    assert DRAFT_INSTRUCTIONS not in SYSTEM_PROMPT
    assert "prepare_draft()" in SYSTEM_PROMPT


def test_draft_rule_tells_writing_a_sentence_apart_from_reading_the_existing_one() -> None:
    # T8.4 (D59): "elabore uma minuta" e "redija a sentença" viraram busca pela sentença existente.
    rule = next(line for line in SYSTEM_PROMPT.splitlines() if line.startswith("7."))

    assert "elaborar, redigir ou escrever" in rule
    assert "antes de qualquer outra ferramenta" in rule
