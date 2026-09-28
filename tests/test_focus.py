"""Processo em foco: gravado na sessão pelas ferramentas (T6.1) e lembrado ao modelo a cada pedido (T6.2). Sem IA."""

import asyncio
from dataclasses import dataclass

import pytest
from pydantic_ai.messages import ModelRequest
from pydantic_ai.models.test import TestModel

from case_assistant import agent_tools
from case_assistant.agent import build_agent
from case_assistant.prompts import DRAFT_INSTRUCTIONS, FOCUS_LABEL
from case_assistant.session import Session, open_session

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"
OTHER_CASE_NUMBER = "0000001-43.2021.8.99.9014"
MISSING_CASE_NUMBER = "0000999-40.2023.8.99.9014"  # dígito verificador certo, mas fora do banco


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


def request_instructions(result) -> list[str | None]:
    return [message.instructions for message in result.all_messages() if isinstance(message, ModelRequest)]


def test_every_turn_reminds_the_model_of_the_focused_case(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    agent = build_agent(TestModel(custom_output_text="ok"))

    with open_session() as session:
        first = agent.run_sync("fale do processo", deps=session)
        session.focused_case_number = REFERENCE_CASE_NUMBER
        second = agent.run_sync("qual o valor da causa?", message_history=first.all_messages(), deps=session)

    assert all(FOCUS_LABEL not in (text or "") for text in request_instructions(first))
    assert f"{FOCUS_LABEL} {REFERENCE_CASE_NUMBER}" in request_instructions(second)[-1]


def test_the_reminder_follows_the_focus_when_it_changes(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    agent = build_agent(TestModel(custom_output_text="ok"))

    with open_session() as session:
        session.focused_case_number = REFERENCE_CASE_NUMBER
        first = agent.run_sync("fale do processo", deps=session)
        session.focused_case_number = OTHER_CASE_NUMBER
        second = agent.run_sync("e as partes?", message_history=first.all_messages(), deps=session)

    assert OTHER_CASE_NUMBER in request_instructions(second)[-1]
    assert REFERENCE_CASE_NUMBER not in request_instructions(second)[-1]


CASE_TOOLS = [agent_tools.find_case, agent_tools.list_parties, agent_tools.list_movements, agent_tools.list_documents]


@pytest.mark.parametrize("tool", CASE_TOOLS, ids=lambda tool: tool.__name__)
def test_case_tools_without_number_use_the_focused_case(tool) -> None:
    with open_session() as session:
        session.focused_case_number = REFERENCE_CASE_NUMBER

        result = call(tool, session)

    assert result["found"] is True
    assert result["case_number"] == REFERENCE_CASE_NUMBER


@pytest.mark.parametrize("tool", CASE_TOOLS, ids=lambda tool: tool.__name__)
def test_an_explicit_number_wins_over_the_focus(tool) -> None:
    with open_session() as session:
        session.focused_case_number = REFERENCE_CASE_NUMBER

        result = call(tool, session, OTHER_CASE_NUMBER)

    assert result["case_number"] == OTHER_CASE_NUMBER


@pytest.mark.parametrize("tool", CASE_TOOLS, ids=lambda tool: tool.__name__)
def test_without_number_and_without_focus_the_tool_asks_for_the_number(tool) -> None:
    with open_session() as session:
        result = call(tool, session)

    assert result == {"found": False, "message": agent_tools.MISSING_CASE_NUMBER_MESSAGE}
    assert "informe o número do processo" in result["message"].lower()


def test_prepare_draft_sends_the_draft_instructions_only_when_there_is_a_basis() -> None:
    with open_session() as session:
        ready = call(agent_tools.prepare_draft, session, REFERENCE_CASE_NUMBER)
        refused = call(agent_tools.prepare_draft, session, OTHER_CASE_NUMBER)

    assert ready["instructions"] == DRAFT_INSTRUCTIONS
    assert "instructions" not in refused


def test_prepare_draft_without_number_uses_the_focused_case() -> None:
    with open_session() as session:
        session.focused_case_number = REFERENCE_CASE_NUMBER
        result = call(agent_tools.prepare_draft, session)

    assert result["case_number"] == REFERENCE_CASE_NUMBER
