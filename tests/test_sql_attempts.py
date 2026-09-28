"""Teto de erros seguidos na consulta livre (T7.6): depois de 2 falhas na mesma pergunta, run_sql para. Sem IA."""

import asyncio
from dataclasses import dataclass

import pytest

from case_assistant import agent_tools
from case_assistant.session import Session, open_session

BROKEN_SQL = "SELECT coluna_que_nao_existe FROM processo"
VALID_SQL = "SELECT COUNT(*) AS total FROM processo"
EMPTY_RESULT_SQL = "SELECT id FROM processo WHERE numero = 'nenhum'"
FIRST_QUESTION = "run-1"
NEXT_QUESTION = "run-2"


@dataclass
class FakeContext:
    """O adaptador usa ctx.deps (a sessão) e ctx.run_id (uma execução do agente por pergunta)."""

    deps: Session
    run_id: str


def run_sql(session: Session, sql: str, run_id: str = FIRST_QUESTION) -> dict:
    return asyncio.run(agent_tools.run_sql(FakeContext(session, run_id), sql))


@pytest.fixture
def session():
    with open_session() as conversation:
        yield conversation


def test_after_two_failures_in_a_row_the_third_query_is_not_run(session) -> None:
    run_sql(session, BROKEN_SQL)
    run_sql(session, BROKEN_SQL)

    result = run_sql(session, VALID_SQL)

    assert result["found"] is False
    assert "Limite de tentativas atingido" in result["message"]
    assert "informe ao usuário" in result["message"]


def test_a_success_between_failures_restarts_the_count(session) -> None:
    run_sql(session, BROKEN_SQL)
    run_sql(session, VALID_SQL)
    run_sql(session, BROKEN_SQL)

    assert run_sql(session, VALID_SQL)["found"] is True


def test_a_new_question_restarts_the_count(session) -> None:
    run_sql(session, BROKEN_SQL)
    run_sql(session, BROKEN_SQL)

    assert run_sql(session, VALID_SQL, run_id=NEXT_QUESTION)["found"] is True


def test_an_empty_result_is_not_a_failure(session) -> None:
    run_sql(session, EMPTY_RESULT_SQL)
    run_sql(session, BROKEN_SQL)

    assert run_sql(session, VALID_SQL)["found"] is True


def test_a_refused_command_counts_as_a_failure(session) -> None:
    run_sql(session, "DELETE FROM processo")
    run_sql(session, BROKEN_SQL)

    assert "Limite de tentativas atingido" in run_sql(session, VALID_SQL)["message"]
