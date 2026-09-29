"""Projeção de custo mensal e ponto de equilíbrio contra um servidor próprio (T13.5, D76). Sem IA."""

import pytest

from case_assistant.cost_projection import ProjectionConfig, Scenario, break_even_answers, mean_cost_per_answer, monthly_projection
from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageRecord

GEMINI = "google:gemini-3.8-flash"
LOCAL = "ollama:qwen3:4b-instruct-2507-q4_K_M"
CONFIG = ProjectionConfig(
    workdays_per_month=22,
    scenarios=[Scenario("Gabinete", users=10, questions_per_user_per_day=20)],
    self_hosted_monthly_usd=1_000.0,
    self_hosted_description="servidor de teste",
    self_hosted_source="fonte de teste",
)


def answer(model: str = GEMINI, recorded_at: str = "2026-09-29T10:00:00") -> UsageRecord:
    return UsageRecord(
        recorded_at=recorded_at, channel="bateria", session_id="s", model=model,
        input_tokens=7_000, output_tokens=100, cache_read_tokens=3_000, requests=2, tools=[], seconds=5.0,
    )


@pytest.fixture
def prices() -> PriceTable:
    return PriceTable.from_environment()  # US$ 0,0036 por resposta de exemplo no Gemini (2026), o dobro em 2027


def test_mean_cost_uses_only_the_chosen_model(prices) -> None:
    records = [answer(), answer(), answer(model=LOCAL)]

    assert mean_cost_per_answer(records, prices, GEMINI) == pytest.approx(0.0036 * 5.2132)


def test_mean_cost_can_be_priced_at_another_date(prices) -> None:
    # O mesmo consumo, no preço que o Google anuncia para 2027.
    assert mean_cost_per_answer([answer()], prices, GEMINI, price_date="2027-01-01") == pytest.approx(2 * 0.0036 * 5.2132)


def test_mean_cost_without_answers_of_the_model_is_unknown(prices) -> None:
    assert mean_cost_per_answer([answer(model=LOCAL)], prices, GEMINI) is None


def test_monthly_projection_multiplies_people_questions_and_workdays(prices) -> None:
    rows = monthly_projection(CONFIG, mean_cost_brl=0.02, usd_brl=prices.usd_brl)

    assert rows[0].name == "Gabinete"
    assert rows[0].answers_per_month == 10 * 20 * 22
    assert rows[0].api_cost_brl == pytest.approx(4_400 * 0.02)
    assert rows[0].self_hosted_brl == pytest.approx(1_000 * prices.usd_brl)


def test_break_even_is_where_the_api_costs_as_much_as_the_server() -> None:
    assert break_even_answers(self_hosted_monthly_brl=1_000.0, mean_cost_brl=0.02) == 50_000


def test_break_even_without_cost_per_answer_is_unknown() -> None:
    assert break_even_answers(self_hosted_monthly_brl=1_000.0, mean_cost_brl=0) is None


def test_the_project_configuration_loads(prices) -> None:
    config = ProjectionConfig.from_environment()

    assert config.workdays_per_month > 0 and config.scenarios and config.self_hosted_monthly_usd > 0
    assert config.self_hosted_source
