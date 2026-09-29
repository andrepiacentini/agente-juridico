"""Interface web em Chainlit, que mostra cada consulta do agente como um passo (E10).

Camada fina sobre o mesmo agente do terminal: aqui não há SQL nem regra de negócio.
Uso: uv run chainlit run app.py
"""

import os
from contextlib import ExitStack

import chainlit as cl
from dotenv import load_dotenv

from case_assistant.agent import ModelNotConfiguredError, build_agent, run_with_retries_async
from case_assistant.session import open_session

MODEL_FAILURE_MESSAGE = "Não consegui obter resposta do modelo: {error}"


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
    try:
        result = await run_with_retries_async(
            agent, message.content, cl.user_session.get("history"), cl.user_session.get("session"), on_retry=_notify
        )
    except Exception as error:  # fronteira da interface: a conversa continua mesmo se o modelo falhar
        await cl.Message(content=MODEL_FAILURE_MESSAGE.format(error=error)).send()
        return
    cl.user_session.set("history", result.all_messages())
    await cl.Message(content=result.output).send()


@cl.on_chat_end
async def end_chat() -> None:
    resources = cl.user_session.get("resources")
    if resources is not None:
        resources.close()


async def _notify(text: str) -> None:
    await cl.Message(content=text).send()
