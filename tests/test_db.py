"""Acesso ao banco: a conexão abre o `desafio.sqlite` só para leitura."""

from contextlib import closing

import shutil
import sqlite3

import pytest
from database_integrity import REFERENCE_DATABASE_SHA256, sha256_of

from case_assistant.db import DEFAULT_DATABASE_PATH, DatabaseNotFoundError, connect

TOTAL_CASES = 10_000
WRITE_STATEMENTS = {
    "insert": "INSERT INTO processo (numero, classe) VALUES ('0000000-00.0000.0.00.0000', 'Teste')",
    "update": "UPDATE processo SET situacao = 'alterado' WHERE id = 1",
    "delete": "DELETE FROM processo WHERE id = 1",
    "drop_table": "DROP TABLE movimentacao",
    "create_table": "CREATE TABLE intruder (id INTEGER)",
}


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


@pytest.mark.parametrize("statement", WRITE_STATEMENTS.values(), ids=WRITE_STATEMENTS.keys())
def test_connect_refuses_writes(statement: str) -> None:
    with closing(connect()) as connection:
        with pytest.raises(sqlite3.OperationalError, match="readonly database"):
            connection.execute(statement)


def test_refused_writes_leave_data_unchanged() -> None:
    with closing(connect()) as connection:
        for statement in WRITE_STATEMENTS.values():
            with pytest.raises(sqlite3.OperationalError):
                connection.execute(statement)
        total = connection.execute("SELECT COUNT(*) AS total FROM processo").fetchone()["total"]
        first_case_status = connection.execute("SELECT situacao FROM processo WHERE id = 1").fetchone()["situacao"]

    assert total == TOTAL_CASES
    assert first_case_status == "julgado"


def test_original_database_matches_reference_hash() -> None:
    assert sha256_of(DEFAULT_DATABASE_PATH) == REFERENCE_DATABASE_SHA256


def test_reference_hash_detects_a_single_changed_byte(tmp_path) -> None:
    database_copy = tmp_path / "copy.sqlite"
    shutil.copyfile(DEFAULT_DATABASE_PATH, database_copy)
    with database_copy.open("r+b") as file:
        file.seek(-1, 2)
        last_byte = file.read(1)
        file.seek(-1, 2)
        file.write(bytes([last_byte[0] ^ 0xFF]))

    assert sha256_of(database_copy) != REFERENCE_DATABASE_SHA256
