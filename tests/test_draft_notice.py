"""Aviso obrigatório no topo da minuta (T8.3, D58): o código garante, com ou sem o modelo lembrar. Sem IA real."""

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from case_assistant.agent import build_agent
from case_assistant.prompts import DRAFT_NOTICE, with_draft_notice
from case_assistant.session import open_session

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"  # tem petição inicial e contestação
CASE_WITHOUT_DOCUMENTS_NUMBER = "0000001-43.2021.8.99.9014"
DRAFT_WITHOUT_NOTICE = "RELATÓRIO\nJoão Ziegler Rocha move ação contra…"


def test_the_notice_is_added_when_the_draft_does_not_start_with_it() -> None:
    assert with_draft_notice(DRAFT_WITHOUT_NOTICE) == f"{DRAFT_NOTICE}\n\n{DRAFT_WITHOUT_NOTICE}"


@pytest.mark.parametrize(
    "draft",
    [
        f"{DRAFT_NOTICE}\n\nRELATÓRIO…",
        f"\n  {DRAFT_NOTICE}\nRELATÓRIO…",
        f"**{DRAFT_NOTICE}**\n\nRELATÓRIO…",
        f"# {DRAFT_NOTICE}\n\nRELATÓRIO…",
    ],
    ids=["plain", "leading_blank_line", "bold", "heading"],
)
def test_a_draft_that_already_starts_with_the_notice_is_kept(draft: str) -> None:
    assert with_draft_notice(draft) == draft


def model_that_forgets_the_notice(case_number: str, answers: list[str]) -> FunctionModel:
    """Chama prepare_draft na primeira ida de cada pergunta e depois responde com o próximo texto, sem o aviso."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if isinstance(messages[-1].parts[-1], ToolReturnPart) or not answers[0].startswith("RELATÓRIO"):
            return ModelResponse(parts=[TextPart(answers.pop(0))])
        return ModelResponse(parts=[ToolCallPart("prepare_draft", {"case_number": case_number})])

    return FunctionModel(respond)


def test_a_draft_answer_gets_the_notice_even_if_the_model_forgets(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    agent = build_agent(model_that_forgets_the_notice(REFERENCE_CASE_NUMBER, [DRAFT_WITHOUT_NOTICE]))

    with open_session() as session:
        result = agent.run_sync(f"elabore a minuta de sentença do processo {REFERENCE_CASE_NUMBER}", deps=session)

    assert result.output.startswith(DRAFT_NOTICE)


def test_a_refusal_gets_no_notice(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    refusal = "RELATÓRIO não é possível: faltam a petição inicial e a contestação."
    agent = build_agent(model_that_forgets_the_notice(CASE_WITHOUT_DOCUMENTS_NUMBER, [refusal]))

    with open_session() as session:
        result = agent.run_sync(f"elabore a minuta do processo {CASE_WITHOUT_DOCUMENTS_NUMBER}", deps=session)

    assert result.output == refusal


def test_the_answer_after_a_draft_gets_no_notice(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    answers = [DRAFT_WITHOUT_NOTICE, "O juiz é Luiz Bonetti Vasconcelos."]
    agent = build_agent(model_that_forgets_the_notice(REFERENCE_CASE_NUMBER, answers))

    with open_session() as session:
        first = agent.run_sync(f"elabore a minuta do processo {REFERENCE_CASE_NUMBER}", deps=session)
        second = agent.run_sync("e quem é o juiz?", message_history=first.all_messages(), deps=session)

    assert second.output == "O juiz é Luiz Bonetti Vasconcelos."
