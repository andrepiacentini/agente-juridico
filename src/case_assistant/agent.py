"""Laço do agente com Pydantic AI: modelo escolhido por `LLM_MODEL`, ferramentas e estado da sessão (E05, E06)."""

import asyncio
import os
import re
import sqlite3
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.agent import EventStreamHandler
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ToolCallPart
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings

from case_assistant.agent_tools import AGENT_TOOLS
from case_assistant.case_number import extract_case_numbers
from case_assistant.citations import cited_document_ids
from case_assistant.prompts import SYSTEM_PROMPT, focus_reminder, with_draft_notice
from case_assistant.session import Session
from case_assistant.tools import SENTENCE_DOCUMENT_TYPES, CaseNotFoundError, initial_petition_ids

MODEL_VARIABLE = "LLM_MODEL"
# Opcional: nível de raciocínio ("low", "true", "false"…). O Gemini precisa de "low" (D30); o modelo local, de nada.
THINKING_VARIABLE = "LLM_THINKING"
# Opcional: modelos que a interface web oferece para troca (T10.3), separados por vírgula, cada um com o raciocínio
# depois de "@": "ollama:qwen3:4b-instruct-2507-q4_K_M,google:gemini-3.8-flash@low". O LLM_MODEL vem sempre primeiro.
MODEL_OPTIONS_VARIABLE = "LLM_MODEL_OPTIONS"
THINKING_SEPARATOR = "@"
BOOLEAN_SETTINGS = {"true": True, "false": False}
# Cache do prompt nos modelos da Anthropic (T14.3, D87): ferramentas e instruções fixas (~3 mil tokens em todo pedido)
# e o histórico da conversa. O lembrete do processo em foco é instrução dinâmica e o Pydantic AI põe a marca antes dele.
# Os outros provedores ignoram estas chaves, então elas vão sempre: o código não tem caminho por fornecedor.
PROMPT_CACHE_SETTINGS: ModelSettings = {
    "anthropic_cache_tool_definitions": True,
    "anthropic_cache_instructions": True,
    "anthropic_cache": True,
}
# Recusas temporárias do serviço do modelo (D41): tentar de novo, avisando o usuário, antes de desistir.
MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 5  # 5 s antes da 2ª tentativa, 10 s antes da 3ª
TEMPORARY_HTTP_STATUSES = {429: "limite de pedidos", 500: "", 502: "", 503: "", 504: ""}
UNREAD_SENTENCE_MESSAGE = (
    "Você citou a sentença [doc {document_id}] sem ler o texto dela. Chame read_document(document_id={document_id}) "
    "e responda com a decisão e os fundamentos que estão no documento."
)
UNREAD_INITIAL_PETITION_MESSAGE = (
    "Os pedidos do autor estão na petição inicial [doc {document_id}], que você ainda não leu. "
    "Chame read_document(document_id={document_id}) e responda de novo a pergunta inteira do usuário, "
    "agora com os pedidos que estão no texto."
)
RELIEF_QUESTION_PATTERN = re.compile(r"\bpedidos?\b", re.IGNORECASE)
# Cada guarda da resposta (número não consultado, sentença não lida, petição não lida) pode devolver a resposta ao
# modelo uma vez.
OUTPUT_RETRIES = 3
UNQUERIED_CASE_MESSAGE = (
    "Você ainda não consultou o processo {case_number} nesta conversa. "
    "Chame find_case(case_number='{case_number}') antes de responder."
)


class ModelNotConfiguredError(RuntimeError):
    """Nenhum modelo foi informado em LLM_MODEL."""


@dataclass(frozen=True)
class ModelOption:
    """Um modelo que a interface pode oferecer, com o raciocínio que ele exige ("" = padrão do modelo)."""

    model: str
    thinking: str


def model_options() -> list[ModelOption]:
    """Os modelos da configuração: o LLM_MODEL (com o LLM_THINKING) e os de LLM_MODEL_OPTIONS, sem repetir."""
    configured = os.environ.get(MODEL_VARIABLE, "").strip()
    if not configured:
        raise ModelNotConfiguredError(f"Defina {MODEL_VARIABLE} no .env (veja .env.example).")
    options = [ModelOption(configured, _configured_thinking())]
    for entry in os.environ.get(MODEL_OPTIONS_VARIABLE, "").split(","):
        model, _, thinking = entry.strip().partition(THINKING_SEPARATOR)
        if model and model not in {option.model for option in options}:
            options.append(ModelOption(model, thinking.strip().lower()))
    return options


def build_agent(model: Model | str | None = None, thinking: str | None = None) -> Agent[Session, str]:
    """Cria o agente. O modelo e o raciocínio vêm da configuração: o código não tem caminho especial por fornecedor.

    Sem `thinking`, o raciocínio vem de LLM_THINKING; a interface web passa o de cada modelo que oferece (T10.3).
    """
    model = model or os.environ.get(MODEL_VARIABLE)
    if not model:
        raise ModelNotConfiguredError(f"Defina {MODEL_VARIABLE} no .env (veja .env.example).")
    agent = Agent(
        model,
        deps_type=Session,
        system_prompt=SYSTEM_PROMPT,
        instructions=_focused_case_instructions,
        tools=AGENT_TOOLS,
        model_settings=_model_settings(_configured_thinking() if thinking is None else thinking),
        retries={"output": OUTPUT_RETRIES},
    )
    agent.output_validator(_require_cited_cases_queried)
    agent.output_validator(_require_cited_sentences_read)
    agent.output_validator(_require_initial_petition_read_for_relief)
    agent.output_validator(_ensure_draft_notice)
    return agent


def _focused_case_instructions(ctx: RunContext[Session]) -> str:
    # Instruções (não system prompt) porque o Pydantic AI as recalcula a cada pedido e não as guarda no histórico:
    # o modelo vê sempre o foco atual, nunca um foco antigo esquecido numa mensagem anterior.
    return focus_reminder(ctx.deps.focused_case_number)


def _require_cited_cases_queried(ctx: RunContext[Session], output: str) -> str:
    # Regra nas instruções não bastou (D51): depois de um processo em foco, o modelo local disse "não consta"
    # de um processo existente sem consultar. Por código, a resposta volta ao modelo até ele consultar.
    question = ctx.prompt if isinstance(ctx.prompt, str) else ""
    queried = _queried_case_numbers(ctx.messages)
    unqueried = [number for number in extract_case_numbers(question) if number not in queried]
    if unqueried:
        raise ModelRetry(UNQUERIED_CASE_MESSAGE.format(case_number=unqueried[0]))
    return output


def _require_cited_sentences_read(ctx: RunContext[Session], output: str) -> str:
    # Regra nas instruções não bastou (D66): o modelo local citava a sentença para "os fundamentos estão lá",
    # sem abrir o documento. Na minuta, a sentença existente não deve ser lida (D57), e o guarda não vale.
    if ctx.deps.draft_run_id == ctx.run_id:
        return output
    read = _read_document_ids(ctx.messages)
    unread = [document_id for document_id in cited_document_ids(output, SENTENCE_DOCUMENT_TYPES) if document_id not in read]
    if unread:
        raise ModelRetry(UNREAD_SENTENCE_MESSAGE.format(document_id=unread[0]))
    return output


async def _require_initial_petition_read_for_relief(ctx: RunContext[Session], output: str) -> str:
    # Regra nas instruções não bastou (T14.7): perguntado sobre os pedidos, o modelo local respondia pelo índice
    # dos documentos, sem abrir a petição inicial, e inventava o conteúdo. Na minuta, quem guia a leitura é ela (D57).
    # Assíncrono como as ferramentas: o Pydantic AI roda validador síncrono noutra thread, e a conexão é desta.
    question = ctx.prompt if isinstance(ctx.prompt, str) else ""
    if ctx.deps.draft_run_id == ctx.run_id or not RELIEF_QUESTION_PATTERN.search(question):
        return output
    read = _read_document_ids(ctx.messages)
    unread = [
        document_id
        for case_number in _asked_case_numbers(question, ctx.deps.focused_case_number)
        for document_id in _initial_petitions(ctx.deps.connection, case_number)
        if document_id not in read
    ]
    if unread:
        raise ModelRetry(UNREAD_INITIAL_PETITION_MESSAGE.format(document_id=unread[0]))
    return output


def _asked_case_numbers(question: str, focused_case_number: str | None) -> list[str]:
    return extract_case_numbers(question) or ([focused_case_number] if focused_case_number else [])


def _initial_petitions(connection: sqlite3.Connection, case_number: str) -> list[int]:
    try:
        return initial_petition_ids(connection, case_number)
    except CaseNotFoundError:
        # Processo inexistente: a ferramenta já disse isso ao modelo, e não há petição a ler.
        return []


def _read_document_ids(messages: list[ModelMessage]) -> set[int]:
    requested = [
        str(part.args_as_dict().get("document_id", ""))
        for message in messages
        for part in message.parts
        if isinstance(part, ToolCallPart) and part.tool_name == "read_document"
    ]
    return {int(document_id) for document_id in requested if document_id.isdigit()}


def _ensure_draft_notice(ctx: RunContext[Session], output: str) -> str:
    # Não depende do modelo lembrar do aviso: se prepare_draft deu base nesta pergunta, a resposta é uma minuta.
    if ctx.deps.draft_run_id == ctx.run_id:
        return with_draft_notice(output)
    return output


def _queried_case_numbers(messages: list[ModelMessage]) -> set[str]:
    """Números de processo passados a alguma ferramenta na conversa, histórico incluído."""
    return {
        number
        for message in messages
        for part in message.parts
        if isinstance(part, ToolCallPart)
        for number in extract_case_numbers(str(part.args_as_dict().get("case_number") or ""))
    }


def _configured_thinking() -> str:
    return os.environ.get(THINKING_VARIABLE, "").strip().lower()


def _model_settings(thinking: str) -> ModelSettings:
    if not thinking:
        return dict(PROMPT_CACHE_SETTINGS)
    return {**PROMPT_CACHE_SETTINGS, "thinking": BOOLEAN_SETTINGS.get(thinking, thinking)}


def run_with_retries(
    agent: Agent[Session, str] | Any,
    question: str,
    history: list[ModelMessage],
    session: Session | None,
    on_retry: Callable[[str], None],
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    """Roda o agente; se o serviço recusar por indisponibilidade temporária, avisa e tenta de novo, com espera crescente."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return agent.run_sync(question, message_history=history, deps=session)
        except ModelAPIError as error:
            wait, notice = _retry_plan(error, attempt)
            on_retry(notice)
            sleep(wait)
    raise AssertionError("inalcançável: a última tentativa devolve ou relança")


async def run_with_retries_async(
    agent: Agent[Session, str] | Any,
    question: str,
    history: list[ModelMessage],
    session: Session | None,
    on_retry: Callable[[str], Awaitable[None]],
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    event_stream_handler: EventStreamHandler[Session] | None = None,
) -> Any:
    """Como run_with_retries, para a interface web: roda no laço assíncrono, na mesma thread da conexão da sessão.

    O event_stream_handler recebe cada chamada de ferramenta enquanto o agente trabalha (T10.2).
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return await agent.run(
                question, message_history=history, deps=session, event_stream_handler=event_stream_handler
            )
        except ModelAPIError as error:
            wait, notice = _retry_plan(error, attempt)
            await on_retry(notice)
            await sleep(wait)
    raise AssertionError("inalcançável: a última tentativa devolve ou relança")


def _retry_plan(error: ModelAPIError, attempt: int) -> tuple[float, str]:
    """Quanto esperar e o que avisar antes da próxima tentativa; relança o erro se não vale tentar de novo."""
    reason = _temporary_failure_reason(error)
    if reason is None or attempt == MAX_ATTEMPTS:
        raise error
    wait = RETRY_WAIT_SECONDS * attempt
    notice = (
        f"O serviço do modelo está indisponível no momento ({reason}). "
        f"Tentando de novo em {wait} s… (tentativa {attempt + 1} de {MAX_ATTEMPTS})"
    )
    return wait, notice


def _temporary_failure_reason(error: ModelAPIError) -> str | None:
    """Motivo legível se a falha for temporária (vale a pena repetir); None se não for (chave inválida, pedido errado)."""
    if not isinstance(error, ModelHTTPError):
        return "sem conexão com o modelo"
    if error.status_code not in TEMPORARY_HTTP_STATUSES:
        return None
    detail = TEMPORARY_HTTP_STATUSES[error.status_code]
    return f"erro {error.status_code}, {detail}" if detail else f"erro {error.status_code}"
