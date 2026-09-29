"""Consumo abaixo de cada resposta do chat web: tokens, custo e tempo, e o total da conversa (T13.3)."""

from case_assistant.citations import brazilian_number
from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageRecord

COST_DECIMALS = 4  # uma pergunta custa frações de centavo: com 2 casas, quase tudo sairia "R$ 0,00"
UNKNOWN_COST = "custo desconhecido"


def usage_footer(answer: UsageRecord, conversation: list[UsageRecord], prices: PriceTable) -> str:
    """Ex.: "7.100 tokens · R$ 0,0188 · 11 s — nesta conversa: 14.200 tokens · R$ 0,0375"."""
    return (
        f"{_tokens(answer.input_tokens + answer.output_tokens)} · {_cost([answer], prices)} · {answer.seconds:.0f} s"
        f" — nesta conversa: {_tokens(sum(record.input_tokens + record.output_tokens for record in conversation))}"
        f" · {_cost(conversation, prices)}"
    )


def _tokens(count: int) -> str:
    return f"{brazilian_number(count, 0)} tokens"


def _cost(records: list[UsageRecord], prices: PriceTable) -> str:
    # Um único custo desconhecido torna o total desconhecido: somar só os conhecidos mostraria um valor errado.
    costs = [prices.cost_brl(record) for record in records]
    if any(cost is None for cost in costs):
        return UNKNOWN_COST
    return f"R$ {brazilian_number(sum(costs), COST_DECIMALS)}"
