"""Painel de consumo: totais por modelo, por conversa e por tipo de pergunta (T13.4, D75). Sem IA."""

import pytest

from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageRecord
from case_assistant.usage_report import question_type, usage_report

GEMINI = "google:gemini-3.8-flash"
LOCAL = "ollama:qwen3:4b-instruct-2507-q4_K_M"


def answer(model: str, session_id: str, tools: list[str], recorded_at: str = "2026-09-29T10:00:00") -> UsageRecord:
    return UsageRecord(
        recorded_at=recorded_at, channel="web", session_id=session_id, model=model,
        input_tokens=7_000, output_tokens=100, cache_read_tokens=3_000, requests=2, tools=tools, seconds=10.0,
    )


@pytest.fixture
def prices() -> PriceTable:
    return PriceTable.from_environment()  # US$ 0,0036 por resposta de exemplo no Gemini, zero no local


@pytest.mark.parametrize(
    ("tools", "expected"),
    [
        (["prepare_draft", "read_document"], "minuta"),
        (["find_case", "read_document"], "leitura de documentos"),
        (["run_sql"], "consulta livre (SQL)"),
        (["search_parties"], "busca"),
        (["find_case", "list_movements"], "cadastro e andamento"),
        ([], "sem consulta"),
    ],
)
def test_question_type_comes_from_the_tools_called(tools: list[str], expected: str) -> None:
    assert question_type(tools) == expected


def test_report_totals_everything_and_splits_by_model(prices) -> None:
    records = [answer(GEMINI, "a", ["find_case"]), answer(GEMINI, "a", []), answer(LOCAL, "b", ["find_case"])]

    report = usage_report(records, prices)

    assert (report.total.answers, report.total.tokens) == (3, 21_300)
    assert report.total.cost_brl == pytest.approx(2 * 0.0036 * 5.2132)
    by_model = {row.label: row for row in report.by_model}
    assert by_model[GEMINI].answers == 2 and by_model[LOCAL].cost_brl == 0


def test_report_lists_conversations_newest_first(prices) -> None:
    records = [
        answer(LOCAL, "antiga", ["find_case"], recorded_at="2026-09-28T09:00:00"),
        answer(GEMINI, "nova", ["find_case"], recorded_at="2026-09-29T09:00:00"),
        answer(LOCAL, "nova", [], recorded_at="2026-09-29T09:01:00"),
    ]

    sessions = usage_report(records, prices).by_session

    assert [session.session_id for session in sessions] == ["nova", "antiga"]
    assert sessions[0].models == [GEMINI, LOCAL] and sessions[0].totals.answers == 2
    assert sessions[0].started_at == "2026-09-29T09:00:00"


def test_report_groups_by_question_type(prices) -> None:
    records = [answer(GEMINI, "a", ["prepare_draft"]), answer(GEMINI, "a", ["prepare_draft"]), answer(GEMINI, "a", [])]

    by_type = {row.label: row.answers for row in usage_report(records, prices).by_question_type}

    assert by_type == {"minuta": 2, "sem consulta": 1}


def test_an_unpriced_answer_makes_the_total_unknown(prices) -> None:
    records = [answer(GEMINI, "a", []), answer("anthropic:claude-sonnet-5", "a", [])]

    assert usage_report(records, prices).total.cost_brl is None


def test_cumulative_cost_follows_the_answers_in_time(prices) -> None:
    records = [answer(GEMINI, "a", [], recorded_at="2026-09-28T10:00:00"), answer(GEMINI, "a", [], recorded_at="2026-09-29T10:00:00")]

    points = usage_report(records, prices).cumulative_cost

    assert [point[0] for point in points] == ["2026-09-28T10:00:00", "2026-09-29T10:00:00"]
    assert points[1][1] == pytest.approx(2 * points[0][1])


def test_an_empty_log_gives_an_empty_report(prices) -> None:
    report = usage_report([], prices)

    assert report.total.answers == 0 and report.by_model == [] and report.by_session == []


def test_report_keeps_its_records_for_the_projection(prices) -> None:
    records = [answer(GEMINI, "a", [])]

    assert usage_report(records, prices).records == records
