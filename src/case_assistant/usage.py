"""Registro de uso de cada resposta: tokens, modelo, sessão, ferramentas e tempo (E13).

Fica num SQLite próprio, nunca no desafio.sqlite (somente leitura). O texto da pergunta não é gravado: o tipo de
pergunta sai das ferramentas chamadas, e o registro não guarda dado de processo.
"""

import json
import logging
import os
import sqlite3
from contextlib import closing
from dataclasses import astuple, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic_ai.messages import ToolCallPart

from case_assistant.db import configured_database_path
from case_assistant.session import Session

logger = logging.getLogger(__name__)

USAGE_PATH_VARIABLE = "USAGE_DB_PATH"
DEFAULT_USAGE_PATH = Path(__file__).resolve().parents[2] / "usage.sqlite"
CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS answer_usage (
        recorded_at TEXT NOT NULL, channel TEXT NOT NULL, session_id TEXT NOT NULL, model TEXT NOT NULL,
        input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL, cache_read_tokens INTEGER NOT NULL,
        requests INTEGER NOT NULL, tools TEXT NOT NULL, seconds REAL NOT NULL,
        cache_write_tokens INTEGER NOT NULL DEFAULT 0
    )
"""
# Registros gravados antes da T14.3 não têm a coluna: ela entra com zero, que é o que eles gravaram no cache.
ADD_CACHE_WRITE_COLUMN = "ALTER TABLE answer_usage ADD COLUMN cache_write_tokens INTEGER NOT NULL DEFAULT 0"


class UsageLogPathError(ValueError):
    """O caminho do registro de uso aponta para o banco do desafio, que é somente leitura."""


@dataclass(frozen=True)
class UsageRecord:
    """Uma resposta do agente: onde (canal), em que conversa, com que modelo e quanto consumiu."""

    recorded_at: str
    channel: str
    session_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    requests: int
    tools: list[str] = field(default_factory=list)
    seconds: float = 0.0
    cache_write_tokens: int = 0


class UsageLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path).expanduser().resolve()
        if self.path == configured_database_path():
            raise UsageLogPathError(f"O registro de uso não pode ficar no banco do desafio ({self.path}).")

    @classmethod
    def from_environment(cls) -> "UsageLog":
        configured = os.environ.get(USAGE_PATH_VARIABLE)
        return cls(Path(configured) if configured else DEFAULT_USAGE_PATH)

    def record(self, usage: UsageRecord) -> None:
        # Uma conexão por gravação: barata, e não disputa a thread com a conexão somente leitura da sessão.
        values = [json.dumps(value) if isinstance(value, list) else value for value in astuple(usage)]
        with closing(self._connect()) as connection, connection:
            connection.execute(f"INSERT INTO answer_usage VALUES ({', '.join('?' * len(values))})", values)

    def records(self, session_id: str | None = None) -> list[UsageRecord]:
        """Todas as respostas registradas, na ordem; com `session_id`, só as de uma conversa."""
        if not self.path.is_file():
            return []
        query = f"SELECT {', '.join(_COLUMNS)} FROM answer_usage WHERE ? IS NULL OR session_id = ? ORDER BY rowid"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, (session_id, session_id)).fetchall()
        return [UsageRecord(**{**dict(zip(_COLUMNS, row)), "tools": json.loads(row[_COLUMNS.index("tools")])}) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute(CREATE_TABLE)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(answer_usage)")}
        if "cache_write_tokens" not in columns:
            connection.execute(ADD_CACHE_WRITE_COLUMN)
        return connection


_COLUMNS = [item.name for item in fields(UsageRecord)]


def usage_record(result: Any, channel: str, session: Session, model: str, seconds: float) -> UsageRecord:
    """O consumo de uma execução do agente (uma pergunta), a partir do que o Pydantic AI contou."""
    usage = result.usage
    return UsageRecord(
        recorded_at=datetime.now().isoformat(timespec="seconds"),
        channel=channel,
        session_id=session.id,
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=usage.cache_read_tokens,
        requests=usage.requests,
        tools=[part.tool_name for message in result.new_messages() for part in message.parts if isinstance(part, ToolCallPart)],
        seconds=seconds,
        cache_write_tokens=usage.cache_write_tokens,
    )


def record_answer(usage_log: "UsageLog", usage: UsageRecord) -> None:
    """Grava o consumo; se o registro falhar, a resposta segue para o usuário e a falha fica no log."""
    try:
        usage_log.record(usage)
    except (OSError, sqlite3.Error) as error:  # fronteira: medir o consumo nunca pode derrubar a conversa
        logger.warning("registro de uso falhou: %s", error, extra={"channel": usage.channel})
