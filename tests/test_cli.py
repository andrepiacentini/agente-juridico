"""Chat no terminal, com um roteiro de perguntas no lugar do teclado e o TestModel no lugar do modelo."""

from pydantic_ai.models.test import TestModel

from case_assistant import cli
from case_assistant.agent import build_agent
from case_assistant.session import open_session


def scripted(*answers: str):
    lines = iter(answers)

    def read(_prompt: str) -> str:
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    return read


def run_chat(model, *questions: str) -> list[str]:
    printed: list[str] = []
    with open_session() as session:
        cli.chat(build_agent(model), session, read=scripted(*questions), write=printed.append)
    return printed


def test_chat_shows_each_tool_call_and_the_answer(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    printed = run_chat(TestModel(call_tools=["find_case"], custom_output_text="Resposta pronta."), "quem é o juiz?", "sair")

    assert any(line.startswith("  → find_case(case_number=") for line in printed)
    assert "Resposta pronta." in "\n".join(printed)


def test_chat_keeps_history_between_questions(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    model = TestModel(call_tools=[])
    captured = []
    original = cli._ask

    def spy(agent, session, question, history, write):
        captured.append(len(history))
        return original(agent, session, question, history, write)

    monkeypatch.setattr(cli, "_ask", spy)
    run_chat(model, "primeira", "segunda", "sair")

    assert captured[0] == 0
    assert captured[1] > 0  # a segunda pergunta vai com o histórico da primeira


def test_chat_ends_with_sair_or_end_of_input(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)

    assert run_chat(TestModel(call_tools=[]), "SAIR")[-1] == cli.GOODBYE
    assert run_chat(TestModel(call_tools=[]))[-1] == cli.GOODBYE  # Ctrl+D (fim da entrada)


def test_model_failure_is_reported_and_chat_goes_on(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    calls = []

    def failing_then_ok(agent, session, question, history, write):
        calls.append(question)
        if len(calls) == 1:
            raise ConnectionError("modelo fora do ar")
        return "ok", history

    monkeypatch.setattr(cli, "_ask", failing_then_ok)
    printed = run_chat(TestModel(call_tools=[]), "primeira", "segunda", "sair")

    assert any("Não consegui obter resposta do modelo: modelo fora do ar" in line for line in printed)
    assert calls == ["primeira", "segunda"]


def test_main_explains_missing_model_configuration(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    assert cli.main() == 1
    assert "LLM_MODEL" in capsys.readouterr().out


def test_main_hides_the_library_banner(monkeypatch) -> None:
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.delenv("PYDANTIC_AI_NO_BANNER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    cli.main()

    import os

    assert os.environ["PYDANTIC_AI_NO_BANNER"] == "1"
