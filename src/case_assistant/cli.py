"""Chat no terminal — primeira interface e plano B da demonstração (E05)."""

import os
from collections.abc import Callable

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ToolCallPart

from case_assistant.agent import ModelNotConfiguredError, build_agent
from case_assistant.session import Session, open_session

WELCOME = "Assistente de processos do TJSC. Pergunte em português; digite 'sair' para encerrar."
PROMPT = "\nVocê: "
EXIT_COMMANDS = {"sair", "exit", "quit"}
GOODBYE = "Até logo."


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
        chat(agent, session)
    return 0


def chat(
    agent: Agent[Session, str],
    session: Session,
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> None:
    """Laço da conversa: pergunta, ferramentas chamadas, resposta; o histórico segue de uma pergunta para a outra."""
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
        try:
            answer, history = _ask(agent, session, question, history, write)
        except Exception as error:  # fronteira da interface: a conversa continua mesmo se o modelo falhar
            write(f"Não consegui obter resposta do modelo: {error}")
            continue
        write(f"\nAssistente: {answer}")
    write(GOODBYE)


def _ask(
    agent: Agent[Session, str],
    session: Session,
    question: str,
    history: list[ModelMessage],
    write: Callable[[str], None] = print,
) -> tuple[str, list[ModelMessage]]:
    result = agent.run_sync(question, message_history=history, deps=session)
    for line in _tool_call_lines(result.new_messages()):
        write(line)
    return result.output, result.all_messages()


def _tool_call_lines(messages: list[ModelMessage]) -> list[str]:
    """Uma linha por ferramenta chamada, com os argumentos — o agente decidindo, à vista de quem usa."""
    lines = []
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                arguments = ", ".join(f"{name}={value!r}" for name, value in part.args_as_dict().items())
                lines.append(f"  → {part.tool_name}({arguments})")
    return lines
