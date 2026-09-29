"""Consumo mostrado abaixo de cada resposta do chat web (T13.3, D74). Sem IA."""

import pytest

from case_assistant.citations import brazilian_number
from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageLog, UsageRecord
from case_assistant.usage_footer import usage_footer

GEMINI = "google:gemini-3.8-flash"
LOCAL = "ollama:qwen3:4b-instruct-2507-q4_K_M"


def answer(model: str = GEMINI, session_id: str = "s1", seconds: float = 11.4) -> UsageRecord:
    return UsageRecord(
        recorded_at="2026-09-29T10:00:00", channel="web", session_id=session_id, model=model,
        input_tokens=7_000, output_tokens=100, cache_read_tokens=3_000, requests=2, tools=["find_case"], seconds=seconds,
    )


@pytest.fixture
def prices() -> PriceTable:
    return PriceTable.from_environment()  # a tabela do projeto: US$ 0,0036 por resposta de exemplo


@pytest.mark.parametrize(
    ("value", "decimals", "expected"),
    [(7100, 0, "7.100"), (0.0187675, 4, "0,0188"), (9_999_999_999, 2, "9.999.999.999,00"), (21495.98, 2, "21.495,98")],
)
def test_brazilian_number(value: float, decimals: int, expected: str) -> None:
    assert brazilian_number(value, decimals) == expected


def test_footer_shows_the_answer_and_the_conversation(prices) -> None:
    footer = usage_footer(answer(), [answer(), answer()], prices)

    assert footer == "7.100 tokens · R$ 0,0188 · 11 s — nesta conversa: 14.200 tokens · R$ 0,0375"


def test_footer_of_the_local_model_shows_zero_cost(prices) -> None:
    assert usage_footer(answer(model=LOCAL), [answer(model=LOCAL)], prices).startswith("7.100 tokens · R$ 0,0000 · 11 s")


def test_footer_says_when_the_cost_is_unknown_instead_of_adding_a_wrong_number(prices) -> None:
    unpriced = answer(model="anthropic:claude-sonnet-5")

    footer = usage_footer(unpriced, [answer(), unpriced], prices)

    assert footer == "7.100 tokens · custo desconhecido · 11 s — nesta conversa: 14.200 tokens · custo desconhecido"


def test_the_log_returns_only_the_records_of_one_conversation(tmp_path) -> None:
    usage_log = UsageLog(tmp_path / "uso.sqlite")
    usage_log.record(answer(session_id="a"))
    usage_log.record(answer(session_id="b"))
    usage_log.record(answer(session_id="a"))

    assert [record.session_id for record in usage_log.records(session_id="a")] == ["a", "a"]
