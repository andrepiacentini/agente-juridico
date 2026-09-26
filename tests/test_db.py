"""Acesso ao banco: a conexão abre o `desafio.sqlite` só para leitura."""

from contextlib import closing

import pytest

from case_assistant.db import DatabaseNotFoundError, connect

TOTAL_CASES = 10_000


def test_connect_reads_all_cases() -> None:
    with closing(connect()) as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM processo").fetchone()

    assert row["total"] == TOTAL_CASES


def test_connect_returns_rows_addressable_by_column_name() -> None:
    with closing(connect()) as connection:
        row = connection.execute("SELECT id, numero FROM processo WHERE id = 1").fetchone()

    assert dict(row) == {"id": 1, "numero": "0000001-43.2021.8.99.9014"}


def test_connect_uses_database_path_from_environment(tmp_path, monkeypatch) -> None:
    missing_database = tmp_path / "does-not-exist.sqlite"
    monkeypatch.setenv("DATABASE_PATH", str(missing_database))

    with pytest.raises(DatabaseNotFoundError, match="does-not-exist.sqlite"):
        connect()
