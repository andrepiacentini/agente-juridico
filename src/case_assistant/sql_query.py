"""Consulta livre em SQL — válvula de escape para perguntas que as ferramentas prontas não cobrem (E04, D03).

É a ferramenta mais arriscada do sistema, por isso a leitura é garantida em três camadas:
1. validação do texto: um único comando, começando por SELECT ou WITH, sem palavras de escrita ou administração;
2. autorizador do próprio SQLite, ativo só durante a consulta: permite leitura e funções, nega todo o resto;
3. conexão aberta em modo somente leitura (D04).
"""

import re
import sqlite3
from typing import Any

# Textos entre aspas simples são removidos antes da validação: "LIKE '%delete%'" não é um comando.
QUOTED_TEXT_PATTERN = re.compile(r"'(?:[^']|'')*'")
FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "create", "alter", "pragma", "attach", "detach", "vacuum", "reindex",
)
FORBIDDEN_KEYWORD_PATTERN = re.compile(r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE)
READ_ONLY_START_PATTERN = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)
AUTHORIZED_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
# O índice de busca (FTS5) consulta internamente este contador de versão; é só leitura. Qualquer outro pragma é negado.
READ_ONLY_INTERNAL_PRAGMA = "data_version"
AUTHORIZATION_ERROR_FRAGMENTS = ("not authorized", "authorization denied")


class QueryRefusedError(Exception):
    """A consulta não é uma leitura simples e não será executada."""


def run_sql(connection: sqlite3.Connection, sql: str) -> dict[str, Any]:
    """Executa uma consulta SQL de leitura (SELECT ou WITH) e devolve colunas e linhas; qualquer outro comando é recusado."""
    try:
        cursor = execute_read_only(connection, _validated(sql))
    except QueryRefusedError as refusal:
        return {"found": False, "message": f"Consulta recusada: {refusal}"}
    except sqlite3.DatabaseError as error:
        if not any(fragment in str(error) for fragment in AUTHORIZATION_ERROR_FRAGMENTS):
            raise
        return {"found": False, "message": "Consulta recusada: o banco negou uma operação que não é leitura."}
    columns = [description[0] for description in cursor.description]
    rows = [list(row) for row in cursor.fetchall()]
    return {"found": True, "columns": columns, "rows": rows, "row_count": len(rows)}


def execute_read_only(connection: sqlite3.Connection, sql: str) -> sqlite3.Cursor:
    """Executa com o autorizador do SQLite ativo: qualquer operação que não seja leitura é negada pelo próprio banco."""
    connection.set_authorizer(_authorize_reads_only)
    try:
        return connection.execute(sql)
    finally:
        connection.set_authorizer(None)


def _validated(sql: str) -> str:
    statement = sql.strip().removesuffix(";").strip()
    if not statement:
        raise QueryRefusedError("a consulta está vazia.")
    without_quoted_text = QUOTED_TEXT_PATTERN.sub("''", statement)
    if ";" in without_quoted_text:
        raise QueryRefusedError("envie um único comando, sem ';' no meio.")
    if not READ_ONLY_START_PATTERN.match(without_quoted_text):
        raise QueryRefusedError("só são aceitas consultas de leitura, começando por SELECT ou WITH.")
    forbidden = FORBIDDEN_KEYWORD_PATTERN.search(without_quoted_text)
    if forbidden:
        raise QueryRefusedError(f"o comando '{forbidden.group(1).upper()}' não é permitido; o banco é somente leitura.")
    return statement


def _authorize_reads_only(action: int, argument: str | None, value: str | None, *_details: Any) -> int:
    if action in AUTHORIZED_ACTIONS:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_PRAGMA and argument == READ_ONLY_INTERNAL_PRAGMA and value is None:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY
