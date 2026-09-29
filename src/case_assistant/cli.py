"""Chat no terminal — primeira interface e plano B da demonstração (E05)."""

import os
import time
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ToolCallPart

from case_assistant.agent import MODEL_VARIABLE, ModelNotConfiguredError, build_agent, run_with_retries
from case_assistant.session import Session, open_session
from case_assistant.tool_display import tool_call_label
from case_assistant.usage import UsageLog, record_answer, usage_record

WELCOME = "Assistente de processos do TJSC. Pergunte em português; digite 'sair' para encerrar."
PROMPT = "\nVocê: "
EXIT_COMMANDS = {"sair", "exit", "quit"}
GOODBYE = "Até logo."
TERMINAL_CHANNEL = "terminal"


def main() -> int:
    load_dotenv()
    # O aviso de observabilidade do Pydantic AI polui o chat; esconde mesmo com um .env antigo.
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    try:
        agent = build_agent()
    except ModelNotConfiguredError as error:
        print(error)
        return 1
    with open_session() as session:
        chat(agent, session, usage_log=UsageLog.from_environment(), model=os.environ.get(MODEL_VARIABLE, ""))
    return 0


def chat(
    agent: Agent[Session, str],
    session: Session,
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
    usage_log: UsageLog | None = None,
    model: str = "",
) -> None:
    """Laço da conversa: pergunta, ferramentas chamadas, resposta; o histórico segue de uma pergunta para a outra.

    Com `usage_log`, o consumo de cada resposta vai para o registro de uso (E13).
    """
    write(WELCOME)
    history: list[ModelMessage] = []
    while True:
        try:
            question = read(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in EXIT_COMMANDS:
            break
        if not question:
            continue
        start = time.monotonic()
        try:
            result = _ask(agent, session, question, history, write)
        except Exception as error:  # fronteira da interface: a conversa continua mesmo se o modelo falhar
            write(f"Não consegui obter resposta do modelo: {error}")
            continue
        if usage_log is not None:
            record_answer(usage_log, usage_record(result, TERMINAL_CHANNEL, session, model, time.monotonic() - start))
        history = result.all_messages()
        write(f"\nAssistente: {result.output}")
    write(GOODBYE)


def _ask(
    agent: Agent[Session, str],
    session: Session,
    question: str,
    history: list[ModelMessage],
    write: Callable[[str], None] = print,
) -> Any:
    result = run_with_retries(agent, question, history, session, on_retry=write)
    for line in _tool_call_lines(result.new_messages()):
        write(line)
    return result


def _tool_call_lines(messages: list[ModelMessage]) -> list[str]:
    """Uma linha por ferramenta chamada, com os argumentos — o agente decidindo, à vista de quem usa."""
    lines = []
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                lines.append(f"  → {tool_call_label(part)}")
    return lines
