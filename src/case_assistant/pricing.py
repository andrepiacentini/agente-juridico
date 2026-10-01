"""Custo de cada resposta: tokens do registro de uso × preço vigente do modelo, em dólar e em real (E13).

Os preços ficam em prices.toml (caminho em PRICES_PATH), com a fonte e a vigência de cada valor: quando o fornecedor
muda a tabela, muda uma linha do arquivo, não o código. Modelo sem preço configurado tem custo desconhecido (None),
nunca zero.
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from case_assistant.usage import UsageRecord

PRICES_PATH_VARIABLE = "PRICES_PATH"
DEFAULT_PRICES_PATH = Path(__file__).resolve().parents[2] / "prices.toml"
TOKENS_PER_PRICE_UNIT = 1_000_000  # os fornecedores cobram por milhão de tokens


@dataclass(frozen=True)
class PricePeriod:
    """Preço por milhão de tokens, em dólar, a partir de uma data (AAAA-MM-DD)."""

    valid_from: str
    input: float
    output: float
    cache_read: float
    # Gravação no cache, quando o fornecedor a cobra à parte (a Anthropic: 1,25 × a entrada); sem ela, conta como entrada.
    cache_write: float | None = None


class PriceTable:
    def __init__(self, periods_by_model: dict[str, list[PricePeriod]], usd_brl: float, exchange_date: str, exchange_source: str) -> None:
        self._periods_by_model = periods_by_model
        self.usd_brl = usd_brl
        self.exchange_date = exchange_date
        self.exchange_source = exchange_source

    @classmethod
    def load(cls, path: Path) -> "PriceTable":
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        periods_by_model = {
            model["model"]: sorted((PricePeriod(**period) for period in model["prices"]), key=lambda period: period.valid_from)
            for model in data["models"]
        }
        exchange = data["exchange"]
        return cls(periods_by_model, exchange["usd_brl"], exchange["date"], exchange["source"])

    @classmethod
    def from_environment(cls) -> "PriceTable":
        configured = os.environ.get(PRICES_PATH_VARIABLE)
        return cls.load(Path(configured) if configured else DEFAULT_PRICES_PATH)

    def cost_usd(self, usage: UsageRecord) -> float | None:
        # A entrada total inclui o que foi lido do cache e o que foi gravado nele; cada parte tem o seu preço.
        price = self._price_in_force(usage.model, usage.recorded_at[:10])
        if price is None:
            return None
        write_price = price.input if price.cache_write is None else price.cache_write
        uncached_input = usage.input_tokens - usage.cache_read_tokens - usage.cache_write_tokens
        return (
            uncached_input * price.input
            + usage.cache_read_tokens * price.cache_read
            + usage.cache_write_tokens * write_price
            + usage.output_tokens * price.output
        ) / TOKENS_PER_PRICE_UNIT

    def cost_brl(self, usage: UsageRecord) -> float | None:
        cost = self.cost_usd(usage)
        return None if cost is None else cost * self.usd_brl

    def _price_in_force(self, model: str, date: str) -> PricePeriod | None:
        in_force = [period for period in self._periods_by_model.get(model, []) if period.valid_from <= date]
        return in_force[-1] if in_force else None
