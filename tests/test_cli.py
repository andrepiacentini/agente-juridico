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

    assert any(line.startswith("  → find_case(") for line in printed)  # o número é opcional (T6.3)
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

    class Answered:
        output = "ok"

        def all_messages(self):
            return []

    def failing_then_ok(agent, session, question, history, write):
        calls.append(question)
        if len(calls) == 1:
            raise ConnectionError("modelo fora do ar")
        return Answered()

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


def test_chat_shows_retry_notice_and_then_the_answer(monkeypatch) -> None:
    from pydantic_ai.exceptions import ModelHTTPError

    from case_assistant import agent as agent_module

    monkeypatch.delenv("LLM_THINKING", raising=False)
    monkeypatch.setattr(agent_module.time, "sleep", lambda _seconds: None)
    real_run_sync = agent_module.Agent.run_sync
    failures = iter([ModelHTTPError(status_code=503, model_name="x", body="alta demanda")])

    def flaky_run_sync(self, *args, **kwargs):
        for failure in failures:
            raise failure
        return real_run_sync(self, *args, **kwargs)

    monkeypatch.setattr(agent_module.Agent, "run_sync", flaky_run_sync)
    printed = run_chat(TestModel(call_tools=[], custom_output_text="Resposta depois da recusa."), "olá", "sair")

    joined = "\n".join(printed)
    assert "indisponível no momento (erro 503). Tentando de novo em 5 s… (tentativa 2 de 3)" in joined
    assert "Resposta depois da recusa." in joined


def test_each_answer_is_recorded_in_the_usage_log(monkeypatch, tmp_path) -> None:
    # E13: o consumo de cada resposta do terminal vai para o registro de uso, com canal e modelo.
    from case_assistant.usage import UsageLog

    monkeypatch.delenv("LLM_THINKING", raising=False)
    usage_log = UsageLog(tmp_path / "uso.sqlite")
    with open_session() as session:
        cli.chat(
            build_agent(TestModel(call_tools=[], custom_output_text="ok")), session,
            read=scripted("olá", "tudo bem?", "sair"), write=lambda _: None, usage_log=usage_log, model="test",
        )

    records = usage_log.records()
    assert [(record.channel, record.model, record.session_id) for record in records] == [
        ("terminal", "test", session.id), ("terminal", "test", session.id)
    ]
    assert all(record.output_tokens > 0 for record in records)
