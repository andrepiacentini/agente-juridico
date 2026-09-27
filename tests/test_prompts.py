"""Descrição do banco para o modelo: completa, curta e com exemplos que de fato rodam."""

import re
from contextlib import closing

import pytest

from case_assistant.db import connect
from case_assistant.prompts import DATABASE_DESCRIPTION
from case_assistant.sql_query import run_sql

# Estimativa conservadora para português: ~3,5 caracteres por token.
MAX_CHARACTERS_FOR_800_TOKENS = 2_800


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
