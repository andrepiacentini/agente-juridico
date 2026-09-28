"""Comando da bateria de avaliação (T9.4, D64): critérios, execução dos casos e placar. Sem IA real."""

import json

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from case_assistant.agent import build_agent
from case_assistant.evaluation import format_report, main, run_case, turn_failures

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"
ANSWER = "O assunto é Acidente de Trânsito [cadastro do processo]."


def test_a_turn_without_criteria_never_fails() -> None:
    assert turn_failures({"ask": "olá"}, "qualquer coisa", tools_called=[]) == []


def test_must_contain_ignores_case_and_accents() -> None:
    turn = {"ask": "…", "must_contain": ["ACIDENTE DE TRANSITO", "não consta"]}

    assert turn_failures(turn, "acidente de trânsito; Nao Consta", tools_called=[]) == []


def test_must_contain_accepts_any_alternative() -> None:
    turn = {"ask": "…", "must_contain": [["não consta", "não encontrado"]]}

    assert turn_failures(turn, "Processo não encontrado.", tools_called=[]) == []
    assert turn_failures(turn, "Resumo do processo.", tools_called=[]) == ["falta: não consta | não encontrado"]


def test_must_not_contain_names_the_forbidden_text_found() -> None:
    turn = {"ask": "…", "must_not_contain": ["3.796,73", ["processo ativo", "processo passivo"]]}

    assert turn_failures(turn, "réu em processo passivo", tools_called=[]) == ["não devia ter: processo passivo"]


def test_must_call_lists_each_missing_tool() -> None:
    turn = {"ask": "…", "must_call": ["find_case", "list_movements"]}

    assert turn_failures(turn, "…", tools_called=["find_case"]) == ["não chamou list_movements"]


def scripted_model(answer: str) -> FunctionModel:
    """Chama find_case com o número da pergunta e depois responde o texto dado."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if isinstance(messages[-1].parts[-1], ToolReturnPart):
            return ModelResponse(parts=[TextPart(answer)])
        return ModelResponse(parts=[ToolCallPart("find_case", {"case_number": REFERENCE_CASE_NUMBER})])

    return FunctionModel(respond)


CASE = {
    "id": "assunto-3161",
    "turns": [
        {"ask": f"qual o assunto do processo {REFERENCE_CASE_NUMBER}?", "must_call": ["find_case"],
         "must_contain": ["Acidente de Trânsito"]},
        {"ask": "e o valor da causa?", "must_call": ["list_parties"], "must_contain": ["3.796,73"]},
    ],
}


@pytest.fixture(autouse=True)
def no_thinking(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)


def test_run_case_checks_each_turn_in_one_conversation() -> None:
    result = run_case(build_agent(scripted_model(ANSWER)), CASE)

    assert result.case_id == "assunto-3161"
    assert [turn.tools_called for turn in result.turns] == [["find_case"], ["find_case"]]
    assert result.turns[0].failures == []
    assert result.turns[1].failures == ["não chamou list_parties", "falta: 3.796,73"]
    assert result.passed is False


def test_a_model_error_fails_the_case_without_stopping_the_battery() -> None:
    def broken(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise RuntimeError("modelo fora do ar")

    result = run_case(build_agent(FunctionModel(broken)), CASE)

    assert result.passed is False
    assert result.turns[0].failures == ["erro do modelo: modelo fora do ar"]
    assert len(result.turns) == 1  # a conversa para no erro: as perguntas seguintes dependem desta


def test_report_shows_each_case_the_failures_and_the_score() -> None:
    passing = run_case(build_agent(scripted_model(ANSWER)), {**CASE, "id": "passa", "turns": CASE["turns"][:1]})
    failing = run_case(build_agent(scripted_model(ANSWER)), CASE)

    report = format_report([passing, failing])

    assert "✓ passa" in report
    assert "✗ assunto-3161" in report
    assert "pergunta 2: não chamou list_parties; falta: 3.796,73" in report
    assert "Placar: 1/2 casos" in report


def test_main_runs_the_chosen_cases_writes_the_answers_and_fails_when_a_case_fails(tmp_path, monkeypatch) -> None:
    golden = tmp_path / "golden.yaml"
    golden.write_text(
        "cases:\n"
        "  - id: um\n    turns:\n      - ask: olá\n        must_contain: [texto que não vem]\n"
        "  - id: dois\n    turns:\n      - ask: olá\n",
        encoding="utf-8",
    )
    output = tmp_path / "respostas.json"
    printed: list[str] = []
    monkeypatch.setattr("builtins.print", lambda text="": printed.append(str(text)))

    exit_code = main(["--golden", str(golden), "--model", "test", "--case", "um", "--output", str(output)])

    assert exit_code == 1
    assert "Placar: 0/1 casos" in "\n".join(printed)
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert [case["id"] for case in saved["cases"]] == ["um"]
    assert saved["cases"][0]["turns"][0]["failures"] == ["falta: texto que não vem"]
