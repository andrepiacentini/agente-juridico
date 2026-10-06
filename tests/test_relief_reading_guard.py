"""Guarda da resposta: pedidos do autor só depois de ler a petição inicial (T14.7). Sem IA real.

O modelo local respondia "quais os pedidos?" pelo índice dos documentos, sem abrir a petição inicial, e inventava
os pedidos (danos morais, artigo de lei, datas). A regra nas instruções não bastou. O FunctionModel reproduz esse
modelo: consulta o processo, responde sem ler e só lê a petição se for devolvido a ele.
"""

from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from case_assistant.agent import build_agent
from case_assistant.session import open_session

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"  # processo 3161
INITIAL_PETITION_ID = 7865
CASE_WITHOUT_DOCUMENTS_NUMBER = "0000001-43.2021.8.99.9014"  # processo 1
UNREAD_ANSWER = "O autor pede indenização por danos morais [doc 7865 — Petição Inicial, 08/01/2024]."
READ_ANSWER = "O autor pede indenização em valor a ser arbitrado [doc 7865 — Petição Inicial, 08/01/2024]."


def model_that_answers_without_reading(calls: list[str], case_number: str = REFERENCE_CASE_NUMBER) -> FunctionModel:
    """Consulta o processo e responde sem ler; devolvido pelo guarda, lê o documento pedido e responde."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        parts = messages[-1].parts
        retry = next((part for part in parts if isinstance(part, RetryPromptPart)), None)
        if retry is not None:
            calls.append(f"retry: {retry.content}")
            return ModelResponse(parts=[ToolCallPart("read_document", {"document_id": INITIAL_PETITION_ID})])
        returned = [part.tool_name for part in parts if isinstance(part, ToolReturnPart)]
        if "read_document" in returned:
            return ModelResponse(parts=[TextPart(READ_ANSWER)])
        if not returned:
            calls.append("consulta")
            return ModelResponse(parts=[ToolCallPart("find_case", {"case_number": case_number})])
        calls.append("responde sem ler")
        return ModelResponse(parts=[TextPart(UNREAD_ANSWER)])

    return FunctionModel(respond)


def ask(question: str, calls: list[str], case_number: str = REFERENCE_CASE_NUMBER) -> str:
    agent = build_agent(model_that_answers_without_reading(calls, case_number))
    with open_session() as session:
        return agent.run_sync(question, deps=session).output


def test_relief_answered_without_reading_the_initial_petition_goes_back_to_the_model(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []

    output = ask(f"Quais são os pedidos apresentados no processo {REFERENCE_CASE_NUMBER}?", calls)

    assert calls[:2] == ["consulta", "responde sem ler"]
    assert f"read_document(document_id={INITIAL_PETITION_ID})" in calls[2]
    assert output == READ_ANSWER


def test_relief_question_about_the_focused_case_also_requires_reading(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_answers_without_reading(calls))

    with open_session() as session:
        first = agent.run_sync(f"qual o assunto do processo {REFERENCE_CASE_NUMBER}?", deps=session)
        calls.clear()
        agent.run_sync("e qual foi o pedido do autor?", message_history=first.all_messages(), deps=session)

    assert any(f"read_document(document_id={INITIAL_PETITION_ID})" in call for call in calls)


def test_a_case_without_initial_petition_needs_no_reading(monkeypatch) -> None:
    # 63% dos processos não têm documento: a resposta certa é "não consta", sem leitura possível.
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []

    ask(f"Quais são os pedidos do processo {CASE_WITHOUT_DOCUMENTS_NUMBER}?", calls, CASE_WITHOUT_DOCUMENTS_NUMBER)

    assert not any(call.startswith("retry") for call in calls)


def test_a_question_that_is_not_about_relief_needs_no_reading(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []

    ask(f"Quem são as partes do processo {REFERENCE_CASE_NUMBER}?", calls)

    assert not any(call.startswith("retry") for call in calls)


def test_an_initial_petition_read_earlier_in_the_conversation_needs_no_new_reading(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_answers_without_reading(calls))

    with open_session() as session:
        first = agent.run_sync(f"Quais os pedidos do processo {REFERENCE_CASE_NUMBER}?", deps=session)
        calls.clear()
        agent.run_sync("repita os pedidos, por favor", message_history=first.all_messages(), deps=session)

    assert not any(call.startswith("retry") for call in calls)
