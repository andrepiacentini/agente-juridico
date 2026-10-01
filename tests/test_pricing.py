"""Custo de cada resposta a partir dos tokens e da tabela de preços (T13.2, D73). Sem IA."""

import pytest

from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageRecord

GEMINI = "google:gemini-3.8-flash"
LOCAL = "ollama:qwen3:4b-instruct-2507-q4_K_M"
TABLE = """
[exchange]
usd_brl = 5.2132
date = "2026-09-28"
source = "PTAX venda, Banco Central do Brasil"

[[models]]
model = "google:gemini-3.8-flash"
source = "https://ai.google.dev/gemini-api/docs/pricing"

[[models.prices]]
valid_from = "2026-09-24"
input = 0.75
output = 3.75
cache_read = 0.075

[[models.prices]]
valid_from = "2027-01-01"
input = 1.50
output = 7.50
cache_read = 0.15

[[models]]
model = "anthropic:claude-sonnet-5-5"
source = "https://platform.claude.com/docs/en/about-claude/pricing"

[[models.prices]]
valid_from = "2026-09-30"
input = 2.00
output = 10.00
cache_read = 0.20
cache_write = 2.50

[[models]]
model = "ollama:qwen3:4b-instruct-2507-q4_K_M"
source = "modelo local"

[[models.prices]]
valid_from = "2026-01-01"
input = 0
output = 0
cache_read = 0
"""


@pytest.fixture
def table(tmp_path) -> PriceTable:
    path = tmp_path / "prices.toml"
    path.write_text(TABLE, encoding="utf-8")
    return PriceTable.load(path)


def answer(model: str = GEMINI, recorded_at: str = "2026-09-29T10:00:00", cache_write_tokens: int = 0) -> UsageRecord:
    return UsageRecord(
        recorded_at=recorded_at, channel="web", session_id="s1", model=model,
        input_tokens=7_000, output_tokens=100, cache_read_tokens=3_000, requests=2, tools=["find_case"], seconds=5.0,
        cache_write_tokens=cache_write_tokens,
    )


def test_cost_matches_the_hand_calculation(table) -> None:
    # (4.000 sem cache × 0,75 + 3.000 em cache × 0,075 + 100 de saída × 3,75) / 1.000.000 = US$ 0,0036
    assert table.cost_usd(answer()) == pytest.approx(0.0036)
    assert table.cost_brl(answer()) == pytest.approx(0.0036 * 5.2132)


def test_the_price_in_force_on_the_answer_date_is_used(table) -> None:
    # O Gemini 3.8 Flash dobra de preço em 01/01/2027 (página oficial, atualizada em 24/09/2026).
    assert table.cost_usd(answer(recorded_at="2027-01-01T00:00:00")) == pytest.approx(0.0072)


def test_the_local_model_costs_nothing_per_token(table) -> None:
    assert table.cost_usd(answer(model=LOCAL)) == 0


def test_a_model_without_price_has_unknown_cost_not_zero(table) -> None:
    assert table.cost_usd(answer(model="anthropic:claude-sonnet-5")) is None
    assert table.cost_brl(answer(model="anthropic:claude-sonnet-5")) is None


def test_an_answer_before_any_price_period_has_unknown_cost(table) -> None:
    assert table.cost_usd(answer(recorded_at="2026-01-01T00:00:00")) is None


def test_exchange_rate_keeps_its_date_and_source(table) -> None:
    assert (table.usd_brl, table.exchange_date, table.exchange_source) == (5.2132, "2026-09-28", "PTAX venda, Banco Central do Brasil")


def test_the_project_price_table_loads_and_prices_both_demo_models() -> None:
    project_table = PriceTable.from_environment()

    assert project_table.cost_usd(answer(model=GEMINI)) > 0
    assert project_table.cost_usd(answer(model=LOCAL)) == 0


CLAUDE = "anthropic:claude-sonnet-5-5"


def test_tokens_written_to_the_cache_are_priced_at_the_write_price(table) -> None:
    # A Anthropic cobra a gravação no cache (5 min) a 1,25 × a entrada; a entrada total já inclui lidos e gravados.
    # (2.000 sem cache × 2,00 + 3.000 lidos × 0,20 + 2.000 gravados × 2,50 + 100 de saída × 10,00) / 1.000.000
    usage = answer(model=CLAUDE, recorded_at="2026-09-30T10:00:00", cache_write_tokens=2_000)

    assert table.cost_usd(usage) == pytest.approx(0.0106)


def test_a_model_without_a_write_price_charges_written_tokens_as_input(table) -> None:
    # O Gemini não cobra gravação à parte: gravado conta como entrada comum.
    assert table.cost_usd(answer(cache_write_tokens=2_000)) == table.cost_usd(answer())
