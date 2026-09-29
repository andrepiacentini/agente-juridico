"""Registro de uso de cada resposta (T13.1, D72): tokens, modelo, sessão e tempo, num arquivo próprio. Sem IA."""

import hashlib
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel
from pydantic_ai.usage import RunUsage

from case_assistant.agent import build_agent
from case_assistant.db import DEFAULT_DATABASE_PATH
from case_assistant.session import open_session
from case_assistant.usage import UsageLog, UsageLogPathError, UsageRecord, usage_record


@pytest.fixture
def usage_log(tmp_path) -> UsageLog:
    return UsageLog(tmp_path / "usage.sqlite")


def sample_record(**changes) -> UsageRecord:
    fields = dict(
        recorded_at="2026-09-29T10:00:00", channel="web", session_id="s1", model="google:gemini-3.8-flash",
        input_tokens=3_000, output_tokens=200, cache_read_tokens=1_000, requests=2, tools=["find_case"], seconds=11.5,
    )
    return UsageRecord(**{**fields, **changes})


def test_a_recorded_answer_is_read_back_as_it_was(usage_log) -> None:
    usage_log.record(sample_record())

    assert usage_log.records() == [sample_record()]


def test_records_keep_their_order(usage_log) -> None:
    usage_log.record(sample_record(session_id="s1"))
    usage_log.record(sample_record(session_id="s2", tools=[]))

    assert [record.session_id for record in usage_log.records()] == ["s1", "s2"]


def test_an_empty_log_has_no_records(usage_log) -> None:
    assert usage_log.records() == []


def test_the_log_refuses_the_path_of_the_case_database() -> None:
    # O desafio.sqlite é somente leitura (AGENTS.md): o registro de uso nunca pode ser gravado nele.
    with pytest.raises(UsageLogPathError):
        UsageLog(DEFAULT_DATABASE_PATH)


def test_recording_does_not_touch_the_case_database(usage_log) -> None:
    before = hashlib.sha256(DEFAULT_DATABASE_PATH.read_bytes()).hexdigest()

    usage_log.record(sample_record())

    assert hashlib.sha256(DEFAULT_DATABASE_PATH.read_bytes()).hexdigest() == before


def test_the_log_path_comes_from_the_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USAGE_DB_PATH", str(tmp_path / "outro.sqlite"))

    UsageLog.from_environment().record(sample_record())

    assert (tmp_path / "outro.sqlite").is_file()


def test_usage_record_takes_tokens_tools_and_model_from_a_real_run(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    agent = build_agent(TestModel(call_tools=["find_case"], custom_output_text="ok"))

    with open_session() as session:
        result = agent.run_sync("qual o assunto do processo?", deps=session)  # sem número: o TestModel inventa um
        record = usage_record(result, channel="terminal", session=session, model="test", seconds=1.25)

    assert record.channel == "terminal" and record.model == "test" and record.seconds == 1.25
    assert record.session_id == session.id
    assert record.tools == ["find_case"]
    assert record.input_tokens > 0 and record.output_tokens > 0 and record.requests == 2
    assert record.recorded_at[:4].isdigit()


def test_each_session_has_its_own_id() -> None:
    with open_session() as first, open_session() as second:
        assert first.id and first.id != second.id


def test_a_failure_to_record_never_breaks_the_answer(caplog) -> None:
    # A resposta chega ao usuário mesmo com o registro indisponível; a falha fica no log.
    from case_assistant.usage import record_answer

    class BrokenLog:
        def record(self, usage) -> None:
            raise OSError("disco cheio")

    record_answer(BrokenLog(), sample_record())

    assert "disco cheio" in caplog.text
