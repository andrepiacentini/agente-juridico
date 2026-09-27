"""Consulta livre (`run_sql`): só leitura, em três camadas — validação, autorizador do SQLite e conexão somente leitura."""

import sqlite3
from contextlib import closing

import pytest

from case_assistant.db import connect, ensure_search_index
from case_assistant.sql_query import execute_read_only, run_sql


@pytest.fixture(scope="module")
def connection():
    with closing(connect()) as database_connection:
        yield database_connection


def test_select_is_accepted(connection) -> None:
    result = run_sql(connection, "SELECT COUNT(*) AS total FROM processo")

    assert result["found"] is True
    assert result["columns"] == ["total"]
    assert result["rows"] == [[10_000]]


def test_with_and_trailing_semicolon_are_accepted(connection) -> None:
    result = run_sql(connection, "with t as (select id from processo where id = 3161) select id from t;")

    assert result["rows"] == [[3161]]


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE processo",
        "delete from processo",
        "INSERT INTO processo (numero) VALUES ('x')",
        "UPDATE processo SET situacao = 'x'",
        "PRAGMA table_info(processo)",
        "ATTACH DATABASE 'x.db' AS x",
        "SELECT 1; DROP TABLE processo",
        "WITH x AS (SELECT 1) DELETE FROM processo",
        "SELECT * FROM processo WHERE id IN (SELECT 1); PRAGMA writable_schema = 1",
        "CREATE TEMP TABLE x AS SELECT 1",
        "",
    ],
    ids=["drop", "delete", "insert", "update", "pragma", "attach", "two_statements", "cte_delete",
         "select_then_pragma", "create_temp", "empty"],
)
def test_anything_but_a_single_read_is_refused_with_reason(connection, sql: str) -> None:
    result = run_sql(connection, sql)

    assert result["found"] is False
    assert result["message"].startswith("Consulta recusada:")


def test_words_inside_quoted_text_do_not_trigger_refusal(connection) -> None:
    result = run_sql(connection, "SELECT COUNT(*) FROM movimentacao WHERE descricao LIKE '%delete%'")

    assert result["found"] is True


def test_replace_function_is_allowed(connection) -> None:
    result = run_sql(connection, "SELECT replace(numero, '-', '') FROM processo WHERE id = 3161")

    assert result["rows"] == [["000000779.2023.8.99.9014"]]


@pytest.mark.parametrize("sql", ["PRAGMA writable_schema = 1", "DELETE FROM processo", "ATTACH DATABASE ':memory:' AS x"])
def test_sqlite_authorizer_blocks_even_without_text_validation(connection, sql: str) -> None:
    with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
        execute_read_only(connection, sql)


def test_authorizer_is_removed_after_the_query(connection) -> None:
    run_sql(connection, "SELECT 1")
    ensure_search_index(connection)  # cria tabelas em TEMP: falharia se o autorizador tivesse ficado ativo

    assert connection.execute("SELECT COUNT(*) FROM temp.document_search").fetchone()[0] == 25_582


def test_reads_used_by_the_model_are_allowed(connection) -> None:
    ensure_search_index(connection)
    schema = run_sql(connection, "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'processo'")
    full_text = run_sql(
        connection, "SELECT COUNT(*) FROM temp.document_search WHERE document_search MATCH '\"dano moral\"'"
    )

    assert schema["rows"] == [["processo"]]
    assert full_text["rows"] == [[550]]  # o FTS5 faz internamente um PRAGMA data_version, só de leitura


def test_blocked_by_sqlite_becomes_refusal_not_exception(connection) -> None:
    result = run_sql(connection, "SELECT load_extension('malicious')")

    assert result["found"] is False
    assert result["message"].startswith("Consulta recusada:")
