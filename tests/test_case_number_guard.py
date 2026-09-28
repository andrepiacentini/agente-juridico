"""Guarda da resposta: número de processo citado na pergunta precisa ter sido consultado (T7.5, D51). Sem IA real.

O modelo local respondeu "não consta" sobre um processo que existe, sem consultar o banco. O `FunctionModel`
reproduz esse modelo: responde direto na primeira vez e só chama a ferramenta se for devolvido a ele.
"""

from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from case_assistant.agent import build_agent
from case_assistant.session import open_session

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"
OTHER_CASE_NUMBER = "0000001-43.2021.8.99.9014"
UNGROUNDED_ANSWER = f"Não consta no banco o processo {OTHER_CASE_NUMBER}."
GROUNDED_ANSWER = "Assunto: Rescisão Contratual c/c Perdas e Danos."


def model_that_skips_the_lookup_once(calls: list[str]) -> FunctionModel:
    """Primeiro responde sem consultar; devolvido pelo guarda, chama find_case; com o resultado, responde."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        last_parts = messages[-1].parts
        if any(isinstance(part, RetryPromptPart) for part in last_parts):
            calls.append("retry")
            return ModelResponse(parts=[ToolCallPart("find_case", {"case_number": OTHER_CASE_NUMBER})])
        if any(isinstance(part, ToolReturnPart) for part in last_parts):
            return ModelResponse(parts=[TextPart(GROUNDED_ANSWER)])
        calls.append("answer")
        return ModelResponse(parts=[TextPart(UNGROUNDED_ANSWER)])

    return FunctionModel(respond)


def test_an_answer_about_an_unqueried_case_number_goes_back_to_the_model(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_skips_the_lookup_once(calls))

    with open_session() as session:
        result = agent.run_sync(f"resuma o processo {OTHER_CASE_NUMBER}", deps=session)

    assert calls == ["answer", "retry"]
    retry_messages = [
        part.content for message in result.all_messages() for part in message.parts if isinstance(part, RetryPromptPart)
    ]
    assert f"find_case(case_number='{OTHER_CASE_NUMBER}')" in retry_messages[0]
    assert result.output == GROUNDED_ANSWER
    assert session.focused_case_number == OTHER_CASE_NUMBER


def test_a_case_number_already_queried_in_the_conversation_needs_no_new_lookup(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_skips_the_lookup_once(calls))

    with open_session() as session:
        first = agent.run_sync(f"resuma o processo {OTHER_CASE_NUMBER}", deps=session)
        calls.clear()
        agent.run_sync(f"e o valor da causa do {OTHER_CASE_NUMBER}?", message_history=first.all_messages(), deps=session)

    assert calls == ["answer"]


def test_a_question_without_case_number_is_not_checked(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_skips_the_lookup_once(calls))

    with open_session() as session:
        agent.run_sync("quantos processos há na comarca de Joinville?", deps=session)

    assert calls == ["answer"]
