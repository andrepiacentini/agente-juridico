"""Como uma chamada de ferramenta aparece para quem usa, no terminal e na web (T10.2, D68). Sem IA."""

import json
from pathlib import Path

import pytest
from pydantic_ai.messages import (
    FunctionToolCallEvent, FunctionToolResultEvent, PartDeltaEvent, PartStartEvent, TextPart, TextPartDelta,
    ThinkingPart, ToolCallPart, ToolReturnPart,
)

from case_assistant.tool_display import (
    ANALYZING_PHASE, ANSWERED_FROM_CONVERSATION, QUERIED_DATABASE, QUERYING_PHASE, STARTING_PHASE, THINKING_PHASE,
    WRITING_PHASE, answer_phase, finished_label, tool_call_label, tool_result_text,
)

TRANSLATION = Path(__file__).parent.parent / ".chainlit" / "translations" / "pt-BR.json"
FIND_CASE_CALL = ToolCallPart("find_case", {"case_number": "0000007-79.2023.8.99.9014"})


def test_label_shows_the_tool_and_its_arguments() -> None:
    part = ToolCallPart("find_case", {"case_number": "0000007-79.2023.8.99.9014"})

    assert tool_call_label(part) == "find_case(case_number='0000007-79.2023.8.99.9014')"


def test_label_of_a_call_without_arguments() -> None:
    assert tool_call_label(ToolCallPart("find_case", {})) == "find_case()"


def test_result_is_readable_json_with_accents() -> None:
    text = tool_result_text({"found": True, "subject": "Acidente de Trânsito"})

    assert text == '{\n  "found": true,\n  "subject": "Acidente de Trânsito"\n}'


def test_text_result_stays_as_it_is() -> None:
    assert tool_result_text("Informe o número do processo.") == "Informe o número do processo."


# Fases da resposta (T14.9): o que o usuário vê enquanto espera, e como o bloco fica no fim.


@pytest.mark.parametrize(
    ("event", "phase"),
    [
        (PartStartEvent(index=0, part=ThinkingPart("…")), THINKING_PHASE),
        (FunctionToolCallEvent(FIND_CASE_CALL), QUERYING_PHASE),
        (FunctionToolResultEvent(ToolReturnPart("find_case", {"found": True})), ANALYZING_PHASE),
        (PartStartEvent(index=0, part=TextPart("O processo")), WRITING_PHASE),
    ],
    ids=["thinking", "tool_call", "tool_result", "text"],
)
def test_each_kind_of_event_starts_its_phase(event, phase: str) -> None:
    assert answer_phase(event) == phase


@pytest.mark.parametrize(
    "event",
    [PartStartEvent(index=0, part=FIND_CASE_CALL), PartDeltaEvent(index=0, delta=TextPartDelta(" judicial"))],
    ids=["tool_call_being_written", "text_delta"],
)
def test_events_that_do_not_change_the_phase(event) -> None:
    assert answer_phase(event) is None


def test_the_phases_are_sentences_that_say_work_is_going_on() -> None:
    assert all(
        phase.endswith("…") for phase in (STARTING_PHASE, THINKING_PHASE, QUERYING_PHASE, ANALYZING_PHASE, WRITING_PHASE)
    )


def test_the_finished_block_says_whether_the_database_was_queried() -> None:
    # Sem consulta, o bloco ficava vazio e sumia: o usuário esperava sem nenhum sinal (T14.9).
    assert finished_label(tools_called=True) == QUERIED_DATABASE == "Consultou o banco de dados"
    assert finished_label(tools_called=False) == ANSWERED_FROM_CONVERSATION


def test_the_interface_adds_no_prefix_to_the_phase_names() -> None:
    # O Chainlit escreve "<prefixo> <nome do passo>"; os nomes das fases já são a frase inteira.
    status = json.loads(TRANSLATION.read_text(encoding="utf-8"))["chat"]["messages"]["status"]

    assert status == {"using": "", "used": ""}
