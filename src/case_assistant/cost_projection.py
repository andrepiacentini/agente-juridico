"""Projeção de custo mensal por cenário de uso e ponto de equilíbrio contra um servidor próprio (T13.5).

Parte do custo médio por resposta medido no registro de uso (não de estimativa) e dos cenários da seção
[projection] do prices.toml. O servidor próprio entra com o custo mensal de uma máquina com GPU na nuvem, citado com
fonte: é uma referência de ordem de grandeza, não um orçamento.
"""

import math
import os
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from case_assistant.pricing import DEFAULT_PRICES_PATH, PRICES_PATH_VARIABLE, PriceTable
from case_assistant.usage import UsageRecord


@dataclass(frozen=True)
class Scenario:
    name: str
    users: int
    questions_per_user_per_day: int


@dataclass(frozen=True)
class ProjectionConfig:
    workdays_per_month: int
    scenarios: list[Scenario]
    self_hosted_monthly_usd: float
    self_hosted_description: str
    self_hosted_source: str

    @classmethod
    def from_environment(cls) -> "ProjectionConfig":
        configured = os.environ.get(PRICES_PATH_VARIABLE)
        data = tomllib.loads(Path(configured or DEFAULT_PRICES_PATH).read_text(encoding="utf-8"))["projection"]
        server = data["self_hosted"]
        return cls(
            workdays_per_month=data["workdays_per_month"],
            scenarios=[Scenario(**scenario) for scenario in data["scenarios"]],
            self_hosted_monthly_usd=server["monthly_usd"],
            self_hosted_description=server["description"],
            self_hosted_source=server["source"],
        )


@dataclass(frozen=True)
class ScenarioCost:
    name: str
    answers_per_month: int
    api_cost_brl: float
    self_hosted_brl: float


def mean_cost_per_answer(
    records: list[UsageRecord], prices: PriceTable, model: str, price_date: str | None = None
) -> float | None:
    """Custo médio, em reais, das respostas registradas de um modelo; com `price_date`, no preço daquela data."""
    answers = [record for record in records if record.model == model]
    if price_date is not None:
        answers = [replace(record, recorded_at=f"{price_date}T00:00:00") for record in answers]
    costs = [prices.cost_brl(record) for record in answers]
    if not costs or any(cost is None for cost in costs):
        return None
    return sum(costs) / len(costs)


def monthly_projection(config: ProjectionConfig, mean_cost_brl: float, usd_brl: float) -> list[ScenarioCost]:
    return [
        ScenarioCost(
            name=scenario.name,
            answers_per_month=(answers := scenario.users * scenario.questions_per_user_per_day * config.workdays_per_month),
            api_cost_brl=answers * mean_cost_brl,
            self_hosted_brl=config.self_hosted_monthly_usd * usd_brl,
        )
        for scenario in config.scenarios
    ]


def break_even_answers(self_hosted_monthly_brl: float, mean_cost_brl: float) -> int | None:
    """Respostas por mês a partir das quais o servidor próprio sai mais barato que pagar por resposta."""
    if mean_cost_brl <= 0:
        return None
    return math.ceil(self_hosted_monthly_brl / mean_cost_brl)
