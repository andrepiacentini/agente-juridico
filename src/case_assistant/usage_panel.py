"""Apresentação do painel de consumo: tabelas em Markdown e gráficos do Plotly (T13.4).

O Chainlit mostra os dois na própria conversa; este módulo não conhece o Chainlit.
"""

import plotly.graph_objects as go

from case_assistant.citations import brazilian_number
from case_assistant.pricing import PriceTable
from case_assistant.usage_report import GroupRow, UsageReport, UsageTotals

EMPTY_PANEL = "Ainda não há respostas registradas."
COST_DECIMALS = 4
RECENT_SESSIONS = 10
SHORT_SESSION_ID = 8


def panel_text(report: UsageReport, prices: PriceTable) -> str:
    if not report.total.answers:
        return EMPTY_PANEL
    total = report.total
    lines = [
        "## Consumo e custo",
        f"**{brazilian_number(total.answers, 0)} respostas** · {brazilian_number(total.tokens, 0)} tokens · "
        f"{_cost(total.cost_brl)} · {total.average_seconds:.0f} s em média por resposta",
        "",
        "### Por modelo",
        "| Modelo | Respostas | Tokens | Custo | Tempo médio |",
        "|---|---:|---:|---:|---:|",
        *(f"| `{row.label}` | {_row(row.totals)} |" for row in report.by_model),
        "",
        "### Por tipo de pergunta",
        "| Tipo | Respostas | Tokens | Custo | Tempo médio |",
        "|---|---:|---:|---:|---:|",
        *(f"| {row.label} | {_row(row.totals)} |" for row in report.by_question_type),
        "",
        "### Conversas mais recentes",
        "| Conversa | Início | Modelos | Respostas | Tokens | Custo | Tempo médio |",
        "|---|---|---|---:|---:|---:|---:|",
        *(
            f"| `{session.session_id[:SHORT_SESSION_ID]}` | {session.started_at.replace('T', ' ')} | "
            f"{', '.join(f'`{model}`' for model in session.models)} | {_row(session.totals)} |"
            for session in report.by_session[:RECENT_SESSIONS]
        ),
        "",
        f"_Preços por milhão de tokens conforme `prices.toml`; câmbio R$ {brazilian_number(prices.usd_brl, 4)} "
        f"({prices.exchange_date}). modelo local: sem custo por token (energia e máquina fora da conta)._",
    ]
    return "\n".join(lines)


def panel_figures(report: UsageReport) -> list[tuple[str, go.Figure]]:
    if not report.total.answers:
        return []
    return [
        ("Custo por modelo", _cost_by_model(report.by_model)),
        ("Tokens por tipo de pergunta", _tokens_by_question_type(report.by_question_type)),
        ("Custo acumulado", _cumulative_cost(report.cumulative_cost)),
    ]


def _row(totals: UsageTotals) -> str:
    return (
        f"{brazilian_number(totals.answers, 0)} | {brazilian_number(totals.tokens, 0)} | "
        f"{_cost(totals.cost_brl)} | {totals.average_seconds:.0f} s"
    )


def _cost(cost_brl: float | None) -> str:
    return "custo desconhecido" if cost_brl is None else f"R$ {brazilian_number(cost_brl, COST_DECIMALS)}"


def _cost_by_model(rows: list[GroupRow]) -> go.Figure:
    figure = go.Figure(go.Bar(x=[row.label for row in rows], y=[row.cost_brl or 0 for row in rows]))
    figure.update_layout(title="Custo por modelo (R$)", yaxis_title="R$")
    return figure


def _tokens_by_question_type(rows: list[GroupRow]) -> go.Figure:
    labels = [row.label for row in rows]
    figure = go.Figure([
        go.Bar(name="entrada", x=labels, y=[row.totals.input_tokens for row in rows]),
        go.Bar(name="saída", x=labels, y=[row.totals.output_tokens for row in rows]),
    ])
    figure.update_layout(title="Tokens por tipo de pergunta", barmode="stack", yaxis_title="tokens")
    return figure


def _cumulative_cost(points: list[tuple[str, float]]) -> go.Figure:
    figure = go.Figure(go.Scatter(x=[moment for moment, _ in points], y=[cost for _, cost in points], mode="lines+markers"))
    figure.update_layout(title="Custo acumulado (R$)", yaxis_title="R$")
    return figure
