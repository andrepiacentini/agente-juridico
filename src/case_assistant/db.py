"""Acesso ao banco: conexão somente leitura ao `desafio.sqlite` e índices de busca em TEMP (E02)."""

import os
import sqlite3
from pathlib import Path

DATABASE_PATH_VARIABLE = "DATABASE_PATH"
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "desafio.sqlite"


class DatabaseNotFoundError(FileNotFoundError):
    """O arquivo do banco não existe no caminho configurado."""


def connect() -> sqlite3.Connection:
    """Abre o banco em modo somente leitura; qualquer escrita é recusada pelo próprio SQLite (D04)."""
    database_path = _configured_database_path()
    if not database_path.is_file():
        raise DatabaseNotFoundError(f"Banco não encontrado em {database_path} (variável {DATABASE_PATH_VARIABLE}).")

    connection = sqlite3.connect(f"{database_path.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _configured_database_path() -> Path:
    configured = os.environ.get(DATABASE_PATH_VARIABLE)
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DATABASE_PATH
