"""Como uma chamada de ferramenta aparece para quem usa, no terminal e na web (T10.2, D68). Sem IA."""

from pydantic_ai.messages import ToolCallPart

from case_assistant.tool_display import tool_call_label, tool_result_text


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
