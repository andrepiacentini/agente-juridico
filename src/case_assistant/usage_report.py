"""Números do painel de consumo: totais do histórico, por modelo, por conversa e por tipo de pergunta (T13.4).

Só cálculo, a partir do registro de uso e da tabela de preços; a apresentação (tabelas e gráficos) fica fora daqui.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageRecord

# O tipo de pergunta sai das ferramentas chamadas (o texto da pergunta não é gravado, D72). A primeira regra que
# casar vale: uma minuta também lê documentos, mas é uma minuta.
QUESTION_TYPE_RULES: list[tuple[str, Callable[[set[str]], bool]]] = [
    ("minuta", lambda tools: "prepare_draft" in tools),
    ("leitura de documentos", lambda tools: "read_document" in tools),
    ("consulta livre (SQL)", lambda tools: "run_sql" in tools),
    ("busca", lambda tools: any(tool.startswith("search_") for tool in tools)),
    ("cadastro e andamento", lambda tools: bool(tools)),
]
NO_QUERY = "sem consulta"


@dataclass(frozen=True)
class UsageTotals:
    answers: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    cost_brl: float | None = 0.0  # None: alguma resposta usou modelo sem preço

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def average_seconds(self) -> float:
        return self.seconds / self.answers if self.answers else 0.0


@dataclass(frozen=True)
class GroupRow:
    label: str
    totals: UsageTotals

    @property
    def answers(self) -> int:
        return self.totals.answers

    @property
    def cost_brl(self) -> float | None:
        return self.totals.cost_brl


@dataclass(frozen=True)
class SessionRow:
    session_id: str
    started_at: str
    models: list[str]
    totals: UsageTotals


@dataclass(frozen=True)
class UsageReport:
    total: UsageTotals
    by_model: list[GroupRow] = field(default_factory=list)
    by_session: list[SessionRow] = field(default_factory=list)
    by_question_type: list[GroupRow] = field(default_factory=list)
    cumulative_cost: list[tuple[str, float]] = field(default_factory=list)  # (data e hora, custo acumulado em R$)
    records: list[UsageRecord] = field(default_factory=list)  # a projeção de custo parte das mesmas respostas


def question_type(tools: Iterable[str]) -> str:
    called = set(tools)
    return next((label for label, matches in QUESTION_TYPE_RULES if matches(called)), NO_QUERY)


def usage_report(records: list[UsageRecord], prices: PriceTable) -> UsageReport:
    ordered = sorted(records, key=lambda record: record.recorded_at)
    return UsageReport(
        total=_totals(ordered, prices),
        by_model=_group(ordered, prices, key=lambda record: record.model),
        by_session=_sessions(ordered, prices),
        by_question_type=_group(ordered, prices, key=lambda record: question_type(record.tools)),
        cumulative_cost=_cumulative_cost(ordered, prices),
        records=ordered,
    )


def _totals(records: list[UsageRecord], prices: PriceTable) -> UsageTotals:
    costs = [prices.cost_brl(record) for record in records]
    return UsageTotals(
        answers=len(records),
        input_tokens=sum(record.input_tokens for record in records),
        output_tokens=sum(record.output_tokens for record in records),
        seconds=sum(record.seconds for record in records),
        cost_brl=None if any(cost is None for cost in costs) else sum(costs),
    )


def _group(records: list[UsageRecord], prices: PriceTable, key: Callable[[UsageRecord], str]) -> list[GroupRow]:
    groups: dict[str, list[UsageRecord]] = {}
    for record in records:
        groups.setdefault(key(record), []).append(record)
    rows = [GroupRow(label, _totals(members, prices)) for label, members in groups.items()]
    return sorted(rows, key=lambda row: -row.answers)


def _sessions(records: list[UsageRecord], prices: PriceTable) -> list[SessionRow]:
    sessions: dict[str, list[UsageRecord]] = {}
    for record in records:
        sessions.setdefault(record.session_id, []).append(record)
    rows = [
        SessionRow(session_id, members[0].recorded_at, list(dict.fromkeys(member.model for member in members)), _totals(members, prices))
        for session_id, members in sessions.items()
    ]
    return sorted(rows, key=lambda row: row.started_at, reverse=True)


def _cumulative_cost(records: list[UsageRecord], prices: PriceTable) -> list[tuple[str, float]]:
    # Respostas sem preço ficam fora da curva: o total do painel já avisa que o custo é desconhecido.
    points, running = [], 0.0
    for record in records:
        cost = prices.cost_brl(record)
        if cost is not None:
            running += cost
            points.append((record.recorded_at, running))
    return points
