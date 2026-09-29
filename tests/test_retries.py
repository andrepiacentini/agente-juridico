"""Novas tentativas quando o serviço do modelo recusa um pedido por indisponibilidade temporária (T5.9). Sem IA."""

import asyncio

import pytest
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError

from case_assistant.agent import MAX_ATTEMPTS, run_with_retries, run_with_retries_async


class ScriptedAgent:
    """Agente de mentira: a cada chamada, lança o próximo erro do roteiro ou devolve o resultado."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def run_sync(self, question, **_kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def run(self, question, **kwargs):
        return self.run_sync(question, **kwargs)


def unavailable(status: int = 503) -> ModelHTTPError:
    return ModelHTTPError(status_code=status, model_name="gemini-3.8-flash", body="alta demanda")


def run(agent):
    notices, waits = [], []
    result = run_with_retries(agent, "pergunta", [], None, on_retry=notices.append, sleep=waits.append)
    return result, notices, waits


def test_unavailable_then_success_returns_the_answer_and_warns_the_user() -> None:
    agent = ScriptedAgent(unavailable(503), "resposta")

    result, notices, waits = run(agent)

    assert result == "resposta"
    assert agent.calls == 2
    assert notices == [
        "O serviço do modelo está indisponível no momento (erro 503). Tentando de novo em 5 s… (tentativa 2 de 3)"
    ]
    assert waits == [5]


def test_gives_up_after_the_last_attempt_warning_before_each_new_one() -> None:
    agent = ScriptedAgent(unavailable(503), unavailable(503), unavailable(503))
    notices, waits = [], []

    with pytest.raises(ModelHTTPError):
        run_with_retries(agent, "pergunta", [], None, on_retry=notices.append, sleep=waits.append)

    assert agent.calls == MAX_ATTEMPTS == 3
    assert notices[0].endswith("(tentativa 2 de 3)") and notices[1].endswith("(tentativa 3 de 3)")
    assert waits == [5, 10]  # espera crescente


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (unavailable(429), "erro 429, limite de pedidos"),
        (unavailable(502), "erro 502"),
        (ModelAPIError(model_name="qwen3", message="Connection error."), "sem conexão com o modelo"),
    ],
    ids=["rate_limit", "bad_gateway", "connection"],
)
def test_other_temporary_failures_are_also_retried(error, reason: str) -> None:
    result, notices, _ = run(ScriptedAgent(error, "resposta"))

    assert result == "resposta"
    assert f"({reason})" in notices[0]


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_permanent_errors_fail_at_once_without_retrying(status: int) -> None:
    agent = ScriptedAgent(unavailable(status), "nunca chega")
    notices, waits = [], []

    with pytest.raises(ModelHTTPError):
        run_with_retries(agent, "pergunta", [], None, on_retry=notices.append, sleep=waits.append)

    assert agent.calls == 1
    assert notices == [] and waits == []


def run_async(agent):
    """A interface web (Chainlit) roda num laço assíncrono: avisos e esperas também são assíncronos (T10.1)."""
    notices, waits = [], []

    async def notify(text: str) -> None:
        notices.append(text)

    async def wait(seconds: float) -> None:
        waits.append(seconds)

    result = asyncio.run(run_with_retries_async(agent, "pergunta", [], None, on_retry=notify, sleep=wait))
    return result, notices, waits


def test_async_version_retries_with_the_same_notices_and_waits() -> None:
    result, notices, waits = run_async(ScriptedAgent(unavailable(503), "resposta"))

    assert result == "resposta"
    assert notices == [
        "O serviço do modelo está indisponível no momento (erro 503). Tentando de novo em 5 s… (tentativa 2 de 3)"
    ]
    assert waits == [5]


def test_async_version_fails_at_once_on_permanent_errors() -> None:
    agent = ScriptedAgent(unavailable(401), "nunca chega")

    with pytest.raises(ModelHTTPError):
        run_async(agent)

    assert agent.calls == 1
