"""Consulta livre que roda sem erro mas não responde à pergunta (T14.5): o resultado leva um lembrete de conferir a
consulta e, se ela não vale, admitir; a falha avisa que não é ausência do dado. Sem IA."""

import asyncio
from dataclasses import dataclass

import pytest

from case_assistant import agent_tools
from case_assistant.session import Session, open_session

VALID_SQL = "SELECT COUNT(*) AS total FROM processo"
# O padrão que o modelo local escreveu no caso pergunta-que-falha: texto de exemplo no lugar do nome.
PLACEHOLDER_SQL = "SELECT COUNT(*) AS total FROM documento WHERE texto LIKE '%[nome de parte]%'"
BROKEN_SQL = "SELECT coluna_que_nao_existe FROM processo"
NOT_FOUND_ANSWER = "Não consta no banco"


@dataclass
class FakeContext:
    deps: Session
    run_id: str = "run-1"


def run_sql(session: Session, sql: str) -> dict:
    return asyncio.run(agent_tools.run_sql(FakeContext(session), sql))


@pytest.fixture
def session():
    with open_session() as conversation:
        yield conversation


def test_a_result_asks_to_check_the_query_against_the_question(session) -> None:
    result = run_sql(session, VALID_SQL)

    assert "compare com a pergunta" in result["check_before_answering"]
    assert "não foi possível obter a resposta" in result["check_before_answering"]
    assert "mostre a consulta" in result["check_before_answering"]


def test_the_check_does_not_change_the_data(session) -> None:
    result = run_sql(session, VALID_SQL)

    assert result["columns"] == ["total"]
    assert result["rows"] == [[10_000]]


def test_a_zero_from_a_placeholder_query_also_carries_the_check(session) -> None:
    result = run_sql(session, PLACEHOLDER_SQL)

    assert result["rows"] == [[0]]
    assert "texto de exemplo" in result["check_before_answering"]


def test_a_failed_query_says_it_is_not_missing_data(session) -> None:
    result = run_sql(session, BROKEN_SQL)

    assert result["found"] is False
    assert f'não diga "{NOT_FOUND_ANSWER}"' in result["note"]


def test_the_attempt_limit_also_says_it_is_not_missing_data(session) -> None:
    run_sql(session, BROKEN_SQL)
    run_sql(session, BROKEN_SQL)

    assert f'não diga "{NOT_FOUND_ANSWER}"' in run_sql(session, VALID_SQL)["message"]
