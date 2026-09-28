"""Estado de uma conversa: com qual banco o agente fala e de qual processo estamos tratando (E05, E06)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass

from case_assistant.db import connect, ensure_search_index


@dataclass
class Session:
    """Memória de trabalho do agente: a conexão somente leitura, o processo em foco (o número CNJ, ou nenhum) e
    os erros seguidos da consulta livre na pergunta atual (T7.6) e a pergunta que pediu uma minuta com base (T8.3)."""

    connection: sqlite3.Connection
    focused_case_number: str | None = None
    failed_sql_attempts: int = 0
    sql_attempts_run_id: str | None = None
    draft_run_id: str | None = None


@contextmanager
def open_session() -> Iterator[Session]:
    """Abre o banco, monta o índice de busca uma vez para toda a conversa (D32) e fecha tudo ao final."""
    with closing(connect()) as connection:
        ensure_search_index(connection)
        yield Session(connection=connection)
