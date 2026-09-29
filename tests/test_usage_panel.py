"""Tabelas e gráficos do painel de consumo (T13.4, D75). Sem IA."""

import pytest

from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageRecord
from case_assistant.usage_panel import panel_figures, panel_text
from case_assistant.usage_report import usage_report

GEMINI = "google:gemini-3.8-flash"
LOCAL = "ollama:qwen3:4b-instruct-2507-q4_K_M"


def answer(model: str, session_id: str, tools: list[str], recorded_at: str) -> UsageRecord:
    return UsageRecord(
        recorded_at=recorded_at, channel="web", session_id=session_id, model=model,
        input_tokens=7_000, output_tokens=100, cache_read_tokens=3_000, requests=2, tools=tools, seconds=10.0,
    )


@pytest.fixture
def report():
    prices = PriceTable.from_environment()
    records = [
        answer(LOCAL, "3f9a1c2e7b", ["find_case"], "2026-09-29T09:00:00"),
        answer(GEMINI, "3f9a1c2e7b", ["prepare_draft", "read_document"], "2026-09-29T09:05:00"),
    ]
    return usage_report(records, prices), prices


def test_panel_text_has_the_summary_and_the_three_tables(report) -> None:
    text = panel_text(*report)

    assert "**2 respostas** · 14.200 tokens · R$ 0,0188" in text
    for heading in ("### Por modelo", "### Por tipo de pergunta", "### Conversas mais recentes"):
        assert heading in text
    assert f"| `{GEMINI}` | 1 | 7.100 | R$ 0,0188 | 10 s |" in text
    assert "| minuta | 1 |" in text
    assert "| `3f9a1c2e` |" in text  # identificador curto da conversa


def test_panel_text_states_the_prices_used(report) -> None:
    text = panel_text(*report)

    assert "câmbio R$ 5,2132 (2026-09-28)" in text
    assert "modelo local: sem custo por token" in text


def test_panel_without_answers_says_so(report) -> None:
    _, prices = report

    assert panel_text(usage_report([], prices), prices) == "Ainda não há respostas registradas."
    assert panel_figures(usage_report([], prices)) == []


def test_panel_has_three_charts_with_titles(report) -> None:
    figures = panel_figures(report[0])

    assert [name for name, _ in figures] == ["Custo por modelo", "Tokens por tipo de pergunta", "Custo acumulado"]
    assert all(figure.data for _, figure in figures)


def test_model_names_in_the_session_table_are_code_so_markdown_does_not_eat_them(report) -> None:
    # ":gemini-3" virava emoji no Markdown do Chainlit e o nome saía "google .8-flash" (D69).
    assert f"`{LOCAL}`, `{GEMINI}`" in panel_text(*report)
