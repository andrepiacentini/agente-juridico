"""Índice de busca por palavras (FTS5) montado em TEMP, sem tocar no arquivo do banco."""

from contextlib import closing

import pytest

from case_assistant.db import connect, create_search_index

REFERENCE_CASE_PLAINTIFF_ID = 5085  # João Ziegler Rocha, autor no processo 3161


@pytest.fixture(scope="module")
def indexed_connection():
    with closing(connect()) as connection:
        create_search_index(connection)
        yield connection


def search_documents(connection, query: str) -> list[int]:
    rows = connection.execute("SELECT rowid FROM temp.document_search WHERE document_search MATCH ?", (query,))
    return [row["rowid"] for row in rows]


def test_finds_documents_containing_a_phrase(indexed_connection) -> None:
    document_ids = search_documents(indexed_connection, '"ônus da prova"')

    assert document_ids
    first_text = indexed_connection.execute(
        "SELECT texto FROM documento WHERE id = ?", (document_ids[0],)
    ).fetchone()["texto"]
    assert "ônus da prova" in first_text.lower()


def test_search_ignores_accents(indexed_connection) -> None:
    assert search_documents(indexed_connection, '"onus da prova"') == search_documents(
        indexed_connection, '"ônus da prova"'
    )


def test_finds_parties_by_name(indexed_connection) -> None:
    rows = indexed_connection.execute(
        "SELECT rowid FROM temp.party_search WHERE party_search MATCH ?", ("ziegler rocha",)
    )

    assert REFERENCE_CASE_PLAINTIFF_ID in [row["rowid"] for row in rows]


def test_index_lives_only_in_temp(indexed_connection) -> None:
    def table_names(schema: str) -> set[str]:
        rows = indexed_connection.execute(f"SELECT name FROM {schema}.sqlite_master WHERE type = 'table'")
        return {row["name"] for row in rows}

    assert {"document_search", "party_search"} <= table_names("temp")
    assert not {"document_search", "party_search"} & table_names("main")
