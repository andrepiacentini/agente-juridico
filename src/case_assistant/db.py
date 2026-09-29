"""Acesso ao banco: conexão somente leitura ao `desafio.sqlite` e índices de busca em TEMP (E02)."""

import os
import sqlite3
from pathlib import Path

from case_assistant.text_normalization import comparable_district, comparable_text

DATABASE_PATH_VARIABLE = "DATABASE_PATH"
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "desafio.sqlite"
# Sem acentos e sem diferença de maiúsculas: "onus" encontra "Ônus".
SEARCH_TOKENIZER = "unicode61 remove_diacritics 2"


class DatabaseNotFoundError(FileNotFoundError):
    """O arquivo do banco não existe no caminho configurado."""


def connect() -> sqlite3.Connection:
    """Abre o banco em modo somente leitura; qualquer escrita é recusada pelo próprio SQLite (D04)."""
    database_path = configured_database_path()
    if not database_path.is_file():
        raise DatabaseNotFoundError(f"Banco não encontrado em {database_path} (variável {DATABASE_PATH_VARIABLE}).")

    connection = sqlite3.connect(f"{database_path.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    # Funções só de comparação, para filtrar sem acento/caixa dentro do SQL (T3.11); não alteram dados.
    connection.create_function("comparable_text", 1, comparable_text, deterministic=True)
    connection.create_function("comparable_district", 1, comparable_district, deterministic=True)
    return connection


def configured_database_path() -> Path:
    """O caminho do desafio.sqlite: DATABASE_PATH, ou o arquivo na raiz do projeto."""
    configured = os.environ.get(DATABASE_PATH_VARIABLE)
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DATABASE_PATH


def create_search_index(connection: sqlite3.Connection) -> None:
    """Monta em TEMP a busca por palavras (FTS5) no texto dos documentos e no nome das partes; o arquivo não muda.

    Leva cerca de 0,4 s no MacBook M1 (T2.5), por isso é chamada uma vez por sessão, e não a cada conexão.
    """
    connection.executescript(f"""
        CREATE VIRTUAL TABLE temp.document_search USING fts5(texto, tokenize='{SEARCH_TOKENIZER}');
        INSERT INTO temp.document_search (rowid, texto) SELECT id, texto FROM main.documento;
        CREATE VIRTUAL TABLE temp.party_search USING fts5(nome, tokenize='{SEARCH_TOKENIZER}');
        INSERT INTO temp.party_search (rowid, nome) SELECT id, nome FROM main.parte;
    """)


def ensure_search_index(connection: sqlite3.Connection) -> None:
    """Cria o índice de busca só se esta conexão ainda não o tiver — o custo é pago uma vez por sessão (D32)."""
    exists = connection.execute(
        "SELECT 1 FROM sqlite_temp_master WHERE type = 'table' AND name = 'document_search'"
    ).fetchone()
    if exists is None:
        create_search_index(connection)
