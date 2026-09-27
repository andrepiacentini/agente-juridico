"""Processo em foco: gravado na sessão sempre que uma ferramenta encontra o processo pelo número (E06). Sem IA."""

import asyncio
from dataclasses import dataclass

import pytest

from case_assistant import agent_tools
from case_assistant.session import Session, open_session

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"
OTHER_CASE_NUMBER = "0000001-43.2021.8.99.9014"
MISSING_CASE_NUMBER = "9999999-99.2099.8.99.9999"


@dataclass
class FakeContext:
    """Os adaptadores só usam ctx.deps; não é preciso um modelo para testá-los."""

    deps: Session


def call(tool, session: Session, *args):
    return asyncio.run(tool(FakeContext(session), *args))


@pytest.mark.parametrize(
    "tool",
    [agent_tools.find_case, agent_tools.list_parties, agent_tools.list_movements, agent_tools.list_documents],
    ids=lambda tool: tool.__name__,
)
def test_tools_that_find_a_case_store_it_as_focus(tool) -> None:
    with open_session() as session:
        call(tool, session, REFERENCE_CASE_NUMBER)

        assert session.focused_case_number == REFERENCE_CASE_NUMBER


def test_focus_is_stored_formatted_even_when_given_as_digits() -> None:
    with open_session() as session:
        call(agent_tools.find_case, session, "00000077920238999014")

        assert session.focused_case_number == REFERENCE_CASE_NUMBER


def test_missing_case_does_not_change_the_focus() -> None:
    with open_session() as session:
        call(agent_tools.find_case, session, REFERENCE_CASE_NUMBER)
        call(agent_tools.find_case, session, MISSING_CASE_NUMBER)

        assert session.focused_case_number == REFERENCE_CASE_NUMBER


def test_a_new_case_replaces_the_focus() -> None:
    with open_session() as session:
        call(agent_tools.find_case, session, REFERENCE_CASE_NUMBER)
        call(agent_tools.list_parties, session, OTHER_CASE_NUMBER)

        assert session.focused_case_number == OTHER_CASE_NUMBER


def test_searches_that_return_many_cases_do_not_change_the_focus() -> None:
    with open_session() as session:
        call(agent_tools.find_case, session, REFERENCE_CASE_NUMBER)
        call(agent_tools.search_cases, session, "plano de saude")
        call(agent_tools.search_parties, session, "Ademir Fabris")
        call(agent_tools.search_text, session, "dano moral")

        assert session.focused_case_number == REFERENCE_CASE_NUMBER
