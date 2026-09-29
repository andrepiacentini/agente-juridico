"""Guarda da resposta: sentença citada tem que ter sido lida (hotfix, D66). Sem IA real.

O modelo local respondia "os fundamentos estão no [doc 7878 — Sentença…]" sem abrir o documento, mesmo com a regra
nas instruções. O FunctionModel reproduz esse modelo: responde citando a sentença e só lê se for devolvido a ele.
"""

from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from case_assistant.agent import build_agent
from case_assistant.session import open_session

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"
SENTENCE_ID = 7878
UNREAD_ANSWER = "Julgado. Os fundamentos estão no [doc 7878 — Sentença, 18/02/2026]."
READ_ANSWER = "Parcialmente procedente, R$ 1.523,18: o montante era excessivo [doc 7878 — Sentença, 18/02/2026]."


def last_parts(messages: list[ModelMessage]) -> list:
    return messages[-1].parts


def model_that_cites_without_reading(calls: list[str], first_calls: tuple[str, ...] = ("find_case",)) -> FunctionModel:
    """Consulta o que for pedido, cita a sentença sem ler; devolvido pelo guarda, lê e responde com o conteúdo."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        retry = next((part for part in last_parts(messages) if isinstance(part, RetryPromptPart)), None)
        if retry is not None:
            calls.append(f"retry: {retry.content}")
            if "read_document" in str(retry.content):
                return ModelResponse(parts=[ToolCallPart("read_document", {"document_id": SENTENCE_ID})])
            return ModelResponse(parts=[ToolCallPart("find_case", {"case_number": REFERENCE_CASE_NUMBER})])
        returned = [part.tool_name for part in last_parts(messages) if isinstance(part, ToolReturnPart)]
        if "read_document" in returned:
            return ModelResponse(parts=[TextPart(READ_ANSWER)])
        if not returned and first_calls:
            calls.append("consulta")
            return ModelResponse(parts=[ToolCallPart(first_calls[0], {"case_number": REFERENCE_CASE_NUMBER})])
        calls.append("responde sem ler")
        return ModelResponse(parts=[TextPart(UNREAD_ANSWER)])

    return FunctionModel(respond)


def test_citing_a_sentence_that_was_not_read_goes_back_to_the_model(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_cites_without_reading(calls))

    with open_session() as session:
        result = agent.run_sync(f"o processo {REFERENCE_CASE_NUMBER} já foi julgado? quais os fundamentos?", deps=session)

    assert calls[:2] == ["consulta", "responde sem ler"]
    assert f"read_document(document_id={SENTENCE_ID})" in calls[2]
    assert result.output == READ_ANSWER


def test_both_guards_can_fire_in_the_same_question(monkeypatch) -> None:
    # Número não consultado (T7.5) e, depois, sentença não lida: cada guarda tem a sua nova tentativa.
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_cites_without_reading(calls, first_calls=()))

    with open_session() as session:
        result = agent.run_sync(f"quais os fundamentos da sentença do processo {REFERENCE_CASE_NUMBER}?", deps=session)

    assert result.output == READ_ANSWER
    assert sum(call.startswith("retry") for call in calls) == 2


def test_a_sentence_read_earlier_in_the_conversation_needs_no_new_reading(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_cites_without_reading(calls))

    with open_session() as session:
        first = agent.run_sync(f"o processo {REFERENCE_CASE_NUMBER} já foi julgado?", deps=session)
        calls.clear()
        agent.run_sync("e qual foi a data?", message_history=first.all_messages(), deps=session)

    assert not any(call.startswith("retry") for call in calls)


def test_citing_a_document_that_is_not_a_sentence_needs_no_reading(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart("A petição inicial é o [doc 7865 — Petição Inicial, 08/01/2024].")])

    with open_session() as session:
        result = build_agent(FunctionModel(respond)).run_sync("quais documentos existem?", deps=session)

    assert result.output.startswith("A petição inicial")


def test_a_draft_may_mention_the_existing_sentence_without_reading_it(monkeypatch) -> None:
    # Na minuta, a sentença existente não deve ser lida (D57): o guarda não vale nessa pergunta.
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls: list[str] = []
    agent = build_agent(model_that_cites_without_reading(calls, first_calls=("prepare_draft",)))

    with open_session() as session:
        result = agent.run_sync(f"elabore a minuta do processo {REFERENCE_CASE_NUMBER}", deps=session)

    assert not any(call.startswith("retry") for call in calls)
    assert "[doc 7878 — Sentença" in result.output
