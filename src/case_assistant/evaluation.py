"""Bateria de avaliação (E09): roda os casos de tests/golden.yaml no agente, confere os critérios e mostra o placar.

Uso: uv run case-assistant-eval [--model MODELO] [--case ID ...] [--output respostas.json]
O formato dos casos está documentado no topo de tests/golden.yaml.
"""

import argparse
import json
import os
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ToolCallPart

from case_assistant.agent import MODEL_VARIABLE, ModelNotConfiguredError, build_agent, run_with_retries
from case_assistant.session import Session, open_session
from case_assistant.text_normalization import comparable_text

DEFAULT_GOLDEN_PATH = Path("tests/golden.yaml")


@dataclass(frozen=True)
class TurnResult:
    ask: str
    answer: str
    tools_called: list[str]
    failures: list[str]
    seconds: float


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    turns: list[TurnResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(turn.failures for turn in self.turns)

    @property
    def seconds(self) -> float:
        return sum(turn.seconds for turn in self.turns)


def load_cases(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["cases"]


def turn_failures(turn: dict[str, Any], answer: str, tools_called: list[str]) -> list[str]:
    """Critérios da pergunta que a resposta não cumpriu, em palavras; lista vazia se passou."""
    text = comparable_text(answer)
    failures = [f"não chamou {tool}" for tool in turn.get("must_call", []) if tool not in tools_called]
    for criterion in turn.get("must_contain", []):
        alternatives = _alternatives(criterion)
        if not any(comparable_text(alternative) in text for alternative in alternatives):
            failures.append(f"falta: {' | '.join(alternatives)}")
    for criterion in turn.get("must_not_contain", []):
        found = [alternative for alternative in _alternatives(criterion) if comparable_text(alternative) in text]
        if found:
            failures.append(f"não devia ter: {found[0]}")
    return failures


def _alternatives(criterion: str | list[str]) -> list[str]:
    return criterion if isinstance(criterion, list) else [criterion]


def run_case(agent: Agent[Session, str], case: dict[str, Any], clock: Callable[[], float] = time.monotonic) -> CaseResult:
    """Uma conversa por caso, numa sessão nova: as perguntas seguem na ordem, com o histórico."""
    result = CaseResult(case_id=case["id"])
    history: list[ModelMessage] = []
    with open_session() as session:
        for turn in case["turns"]:
            start = clock()
            try:
                run = run_with_retries(agent, turn["ask"], history, session, on_retry=print)
            except Exception as error:  # fronteira da bateria: um caso que quebra não derruba os outros
                result.turns.append(TurnResult(turn["ask"], "", [], [f"erro do modelo: {error}"], clock() - start))
                break  # as perguntas seguintes dependem desta
            tools_called = _tool_names(run.new_messages())
            failures = turn_failures(turn, run.output, tools_called)
            result.turns.append(TurnResult(turn["ask"], run.output, tools_called, failures, clock() - start))
            history = run.all_messages()
    return result


def _tool_names(messages: list[ModelMessage]) -> list[str]:
    return [part.tool_name for message in messages for part in message.parts if isinstance(part, ToolCallPart)]


def format_report(results: list[CaseResult]) -> str:
    return "\n".join([*(format_case(case) for case in results), "", format_score(results)])


def format_case(case: CaseResult) -> str:
    lines = [f"{'✓' if case.passed else '✗'} {case.case_id} ({case.seconds:.0f} s)"]
    lines += [
        f"    pergunta {number}: {'; '.join(turn.failures)}"
        for number, turn in enumerate(case.turns, start=1)
        if turn.failures
    ]
    return "\n".join(lines)


def format_score(results: list[CaseResult]) -> str:
    passed = sum(case.passed for case in results)
    return f"Placar: {passed}/{len(results)} casos ({sum(case.seconds for case in results):.0f} s)"


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_arguments(argv)
    load_dotenv()
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    try:
        agent = build_agent(arguments.model)
    except ModelNotConfiguredError as error:
        print(error)
        return 2
    cases = [case for case in load_cases(arguments.golden) if not arguments.case or case["id"] in arguments.case]
    results = []
    for case in cases:
        results.append(run_case(agent, case))
        print(format_case(results[-1]))  # cada caso ao terminar: a bateria inteira leva minutos no modelo local
    print(f"\n{format_score(results)}")
    if arguments.output:
        _save_answers(arguments.output, arguments.model or os.environ.get(MODEL_VARIABLE, ""), results)
    return 0 if all(case.passed for case in results) else 1


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="case-assistant-eval", description="Roda a bateria de avaliação do agente.")
    parser.add_argument("--model", help=f"modelo a usar (padrão: {MODEL_VARIABLE} do .env)")
    parser.add_argument("--case", action="append", help="id de um caso a rodar; repita para vários (padrão: todos)")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN_PATH, help="arquivo de casos")
    parser.add_argument("--output", type=Path, help="grava as respostas e as falhas neste arquivo JSON")
    return parser.parse_args(argv)


def _save_answers(path: Path, model: str, results: list[CaseResult]) -> None:
    report = {
        "date": date.today().isoformat(),
        "model": model,
        "score": f"{sum(case.passed for case in results)}/{len(results)}",
        "cases": [{"id": case.case_id, "passed": case.passed, "turns": [asdict(turn) for turn in case.turns]} for case in results],
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
