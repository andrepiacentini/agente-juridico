"""Interface web em Chainlit, que mostra cada consulta do agente como um passo (E10).

Camada fina sobre o mesmo agente do terminal: aqui não há SQL nem regra de negócio.
Uso: uv run chainlit run app.py
"""

import os
from collections.abc import AsyncIterable
from contextlib import ExitStack

import chainlit as cl
from dotenv import load_dotenv
from pydantic_ai import RunContext
from pydantic_ai.agent import EventStreamHandler
from pydantic_ai.messages import AgentStreamEvent, FunctionToolCallEvent, FunctionToolResultEvent

from case_assistant.agent import ModelNotConfiguredError, build_agent, run_with_retries_async
from case_assistant.session import Session, open_session
from case_assistant.tool_display import tool_call_label, tool_result_text

MODEL_FAILURE_MESSAGE = "Não consegui obter resposta do modelo: {error}"
QUERIES_STEP_NAME = "Consultas ao banco"


@cl.on_chat_start
async def start_chat() -> None:
    """Uma sessão por conversa: conexão somente leitura, processo em foco e histórico próprios."""
    load_dotenv()
    # O aviso de observabilidade do Pydantic AI polui o log do servidor; esconde mesmo com um .env antigo.
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    try:
        agent = build_agent()
    except ModelNotConfiguredError as error:
        await cl.Message(content=str(error)).send()
        return
    resources = ExitStack()
    cl.user_session.set("resources", resources)
    cl.user_session.set("session", resources.enter_context(open_session()))
    cl.user_session.set("agent", agent)
    cl.user_session.set("history", [])


@cl.on_message
async def answer(message: cl.Message) -> None:
    agent = cl.user_session.get("agent")
    if agent is None:
        return  # modelo não configurado: o aviso já foi mostrado ao abrir o chat
    # As consultas ficam agrupadas num passo aberto antes de o agente começar: a resposta, enviada depois,
    # aparece abaixo delas, e cada consulta pode ser aberta para conferir o que o agente leu.
    queries = cl.Step(name=QUERIES_STEP_NAME, type="run", default_open=True)
    await queries.send()
    try:
        result = await run_with_retries_async(
            agent,
            message.content,
            cl.user_session.get("history"),
            cl.user_session.get("session"),
            on_retry=_notify,
            event_stream_handler=_tool_steps_under(queries),
        )
    except Exception as error:  # fronteira da interface: a conversa continua mesmo se o modelo falhar
        await queries.remove()
        await cl.Message(content=MODEL_FAILURE_MESSAGE.format(error=error)).send()
        return
    await queries.update()
    cl.user_session.set("history", result.all_messages())
    await cl.Message(content=result.output).send()


@cl.on_chat_end
async def end_chat() -> None:
    resources = cl.user_session.get("resources")
    if resources is not None:
        resources.close()


async def _notify(text: str) -> None:
    await cl.Message(content=text).send()


def _tool_steps_under(parent: cl.Step) -> EventStreamHandler[Session]:
    """Cada chamada de ferramenta vira um passo dentro de `parent`, aberto quando começa, preenchido quando termina e
    recolhido em seguida: quem usa vê o agente decidir e pode conferir o que ele leu (fundamentação visível)."""

    async def show_tool_steps(ctx: RunContext[Session], events: AsyncIterable[AgentStreamEvent]) -> None:
        await _show_tool_steps(parent, events)

    return show_tool_steps


async def _show_tool_steps(parent: cl.Step, events: AsyncIterable[AgentStreamEvent]) -> None:
    open_steps: dict[str, cl.Step] = {}
    async for event in events:
        if isinstance(event, FunctionToolCallEvent):
            step = cl.Step(
                name=tool_call_label(event.part), type="tool", language="json", parent_id=parent.id, auto_collapse=True
            )
            step.input = tool_result_text(event.part.args_as_dict())
            await step.send()
            open_steps[event.part.tool_call_id] = step
        elif isinstance(event, FunctionToolResultEvent):
            step = open_steps.pop(event.part.tool_call_id, None)
            if step is not None:
                step.output = tool_result_text(event.part.content)
                await step.update()
