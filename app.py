"""Interface web em Chainlit, que mostra cada consulta do agente como um passo (E10).

Camada fina sobre o mesmo agente do terminal: aqui não há SQL nem regra de negócio.
Uso: uv run chainlit run app.py
"""

import logging
import os
import time
from collections.abc import AsyncIterable
from contextlib import ExitStack

import chainlit as cl
from chainlit.input_widget import Select
from dotenv import load_dotenv
from pydantic_ai import RunContext
from pydantic_ai.agent import EventStreamHandler
from pydantic_ai.messages import AgentStreamEvent, FunctionToolCallEvent, FunctionToolResultEvent

from case_assistant.agent import ModelNotConfiguredError, ModelOption, build_agent, model_options, run_with_retries_async
from case_assistant.session import Session, open_session
from case_assistant.tool_display import tool_call_label, tool_result_text
from case_assistant.cost_projection import ProjectionConfig
from case_assistant.pricing import PriceTable
from case_assistant.usage import UsageLog, record_answer, usage_record
from case_assistant.usage_footer import usage_footer
from case_assistant.usage_panel import panel_figures, panel_text
from case_assistant.usage_report import usage_report

logger = logging.getLogger(__name__)

MODEL_FAILURE_MESSAGE = "Não consegui obter resposta do modelo: {error}"
WEB_CHANNEL = "web"
# Botão junto do campo de mensagem (T13.4): monta o painel sem chamar o agente, então não consome tokens.
USAGE_COMMAND = "Ver consumo"
USAGE_ACTION = "usage_panel"
USAGE_COMMANDS = [
    {"id": USAGE_COMMAND, "icon": "chart-column", "description": "Tokens e custo: histórico, por modelo e por conversa", "button": True}
]
QUERIES_STEP_NAME = "o banco de dados"  # a interface mostra "Consultou o banco de dados"
MODEL_SETTING = "model"
# As 4 perguntas do edital sobre o processo de referência, com o mesmo texto da bateria de avaliação (T10.4).
REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"
WELCOME_STARTERS = [
    cl.Starter(
        label="Resumo do processo",
        message=f"Resuma o processo {REFERENCE_CASE_NUMBER}, destacando os principais fatos e o andamento processual.",
    ),
    cl.Starter(
        label="Partes, juiz e advogados",
        message=f"Quem são as partes, o magistrado e os advogados do processo {REFERENCE_CASE_NUMBER}? "
        "Quais são os pedidos apresentados?",
    ),
    cl.Starter(
        label="Já foi julgado?",
        message=f"O processo {REFERENCE_CASE_NUMBER} já foi julgado? Se sim, qual foi a decisão e quais foram seus fundamentos?",
    ),
    cl.Starter(
        label="Minuta de sentença",
        message=f"Elabore uma minuta de sentença para o processo {REFERENCE_CASE_NUMBER}, "
        "com base nos fatos e documentos disponíveis.",
    ),
]
MODEL_CHANGED_MESSAGE = "A partir de agora, respondo com o modelo `{model}`. A conversa e o processo em foco continuam."


@cl.set_starters
async def welcome_starters(user: cl.User | None = None, language: str | None = None) -> list[cl.Starter]:
    """Tela de boas-vindas: quem nunca viu o sistema clica numa pergunta do edital e vê o agente trabalhar."""
    return WELCOME_STARTERS


@cl.on_chat_start
async def start_chat() -> None:
    """Uma sessão por conversa: conexão somente leitura, processo em foco e histórico próprios."""
    load_dotenv()
    # O aviso de observabilidade do Pydantic AI polui o log do servidor; esconde mesmo com um .env antigo.
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    try:
        options = model_options()
    except ModelNotConfiguredError as error:
        await cl.Message(content=str(error)).send()
        return
    # A troca de modelo fica nas configurações do chat, com os modelos do .env (T10.3): a mesma pergunta nos dois.
    await cl.ChatSettings(
        [Select(id=MODEL_SETTING, label="Modelo", values=[option.model for option in options], initial_index=0)]
    ).send()
    cl.user_session.set("model_options", options)
    cl.user_session.set("usage_log", UsageLog.from_environment())
    cl.user_session.set("prices", _load_prices())
    cl.user_session.set("projection", _load_projection())
    await cl.context.emitter.set_commands(USAGE_COMMANDS)
    agent = _build_agent(options[0])
    resources = ExitStack()
    cl.user_session.set("resources", resources)
    cl.user_session.set("session", resources.enter_context(open_session()))
    cl.user_session.set("agent", agent)
    cl.user_session.set("history", [])


@cl.on_message
async def answer(message: cl.Message) -> None:
    if message.command == USAGE_COMMAND:
        await _show_usage_panel()
        return
    agent = cl.user_session.get("agent")
    if agent is None:
        return  # modelo não configurado: o aviso já foi mostrado ao abrir o chat
    # As consultas ficam agrupadas num passo aberto antes de o agente começar: a resposta, enviada depois,
    # aparece abaixo delas, e cada consulta pode ser aberta para conferir o que o agente leu.
    queries = cl.Step(name=QUERIES_STEP_NAME, type="run", default_open=True)
    await queries.send()
    start = time.monotonic()
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
    usage = usage_record(result, WEB_CHANNEL, cl.user_session.get("session"), cl.user_session.get("model"), time.monotonic() - start)
    if usage.tools:
        await queries.update()
    else:
        await queries.remove()  # respondeu pelo histórico: um bloco "Consultou o banco de dados" vazio seria falso
    record_answer(cl.user_session.get("usage_log"), usage)
    cl.user_session.set("history", result.all_messages())
    await cl.Message(content=result.output + _footer(usage), actions=_usage_actions()).send()


@cl.on_settings_update
async def change_model(settings: dict[str, str]) -> None:
    """Troca só o agente: a sessão (histórico e processo em foco) continua a mesma."""
    options: list[ModelOption] = cl.user_session.get("model_options") or []
    chosen = next((option for option in options if option.model == settings.get(MODEL_SETTING)), None)
    if chosen is None:
        return
    cl.user_session.set("agent", _build_agent(chosen))
    await cl.Message(content=MODEL_CHANGED_MESSAGE.format(model=chosen.model)).send()


@cl.on_chat_end
async def end_chat() -> None:
    resources = cl.user_session.get("resources")
    if resources is not None:
        resources.close()


@cl.action_callback(USAGE_ACTION)
async def open_usage_panel(action: cl.Action) -> None:
    """O mesmo painel do comando, num clique, pelo botão embaixo de cada resposta."""
    await _show_usage_panel()


def _usage_actions() -> list[cl.Action]:
    if cl.user_session.get("prices") is None:
        return []
    return [cl.Action(name=USAGE_ACTION, payload={}, label=USAGE_COMMAND, icon="chart-column")]


async def _show_usage_panel() -> None:
    """Tabelas e gráficos do consumo registrado, na própria conversa."""
    prices = cl.user_session.get("prices")
    if prices is None:
        await cl.Message(content="O painel precisa da tabela de preços (prices.toml), que não foi encontrada.").send()
        return
    report = usage_report(cl.user_session.get("usage_log").records(), prices)
    charts = [cl.Plotly(name=name, figure=figure, display="inline") for name, figure in panel_figures(report)]
    text = panel_text(report, prices, projection=cl.user_session.get("projection"))
    await cl.Message(content=text, elements=charts).send()


def _load_projection() -> ProjectionConfig | None:
    try:
        return ProjectionConfig.from_environment()
    except (OSError, KeyError, ValueError) as error:  # sem cenários, o painel mostra só o consumo
        logger.warning("cenários de projeção indisponíveis: %s", error)
        return None


def _load_prices() -> PriceTable | None:
    try:
        return PriceTable.from_environment()
    except (OSError, KeyError, ValueError) as error:  # sem tabela de preços, o chat funciona sem o rodapé de custo
        logger.warning("tabela de preços indisponível: %s", error)
        return None


def _footer(usage) -> str:
    """Consumo da resposta e da conversa, em itálico, abaixo do texto (T13.3)."""
    prices = cl.user_session.get("prices")
    if prices is None:
        return ""
    conversation = cl.user_session.get("usage_log").records(session_id=usage.session_id)
    return f"\n\n*{usage_footer(usage, conversation, prices)}*"


def _build_agent(option: ModelOption):
    cl.user_session.set("model", option.model)  # o registro de uso anota com qual modelo cada resposta saiu
    return build_agent(option.model, thinking=option.thinking)


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
