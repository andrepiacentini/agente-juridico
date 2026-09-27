"""Estado da sessão: a conexão com o banco (já com o índice de busca) e o processo em foco."""

import sqlite3

import pytest

from case_assistant.session import open_session

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"


def test_new_session_has_read_only_connection_and_no_focus() -> None:
    with open_session() as session:
        assert session.focused_case_number is None
        assert session.connection.execute("SELECT COUNT(*) FROM processo").fetchone()[0] == 10_000
        with pytest.raises(sqlite3.OperationalError, match="readonly database"):
            session.connection.execute("DELETE FROM processo")


def test_session_builds_the_search_index_once_when_opened() -> None:
    with open_session() as session:
        indexed = session.connection.execute("SELECT COUNT(*) FROM temp.document_search").fetchone()[0]

    assert indexed == 25_582


def test_focused_case_can_be_set_and_changed() -> None:
    with open_session() as session:
        session.focused_case_number = REFERENCE_CASE_NUMBER
        assert session.focused_case_number == REFERENCE_CASE_NUMBER


def test_connection_is_closed_when_the_session_ends() -> None:
    with open_session() as session:
        connection = session.connection

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")
