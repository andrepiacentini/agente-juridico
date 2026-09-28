"""Laço do agente com Pydantic AI: modelo escolhido por `LLM_MODEL`, ferramentas e estado da sessão (E05, E06)."""

import os
import time
from collections.abc import Callable
from typing import Any

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ToolCallPart
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings

from case_assistant.agent_tools import AGENT_TOOLS
from case_assistant.case_number import extract_case_numbers
from case_assistant.prompts import SYSTEM_PROMPT, focus_reminder, with_draft_notice
from case_assistant.session import Session

MODEL_VARIABLE = "LLM_MODEL"
# Opcional: nível de raciocínio ("low", "true", "false"…). O Gemini precisa de "low" (D30); o modelo local, de nada.
THINKING_VARIABLE = "LLM_THINKING"
BOOLEAN_SETTINGS = {"true": True, "false": False}
# Recusas temporárias do serviço do modelo (D41): tentar de novo, avisando o usuário, antes de desistir.
MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 5  # 5 s antes da 2ª tentativa, 10 s antes da 3ª
TEMPORARY_HTTP_STATUSES = {429: "limite de pedidos", 500: "", 502: "", 503: "", 504: ""}
UNQUERIED_CASE_MESSAGE = (
    "Você ainda não consultou o processo {case_number} nesta conversa. "
    "Chame find_case(case_number='{case_number}') antes de responder."
)


class ModelNotConfiguredError(RuntimeError):
    """Nenhum modelo foi informado em LLM_MODEL."""


def build_agent(model: Model | str | None = None) -> Agent[Session, str]:
    """Cria o agente. O modelo e o raciocínio vêm da configuração: o código não tem caminho especial por fornecedor."""
    model = model or os.environ.get(MODEL_VARIABLE)
    if not model:
        raise ModelNotConfiguredError(f"Defina {MODEL_VARIABLE} no .env (veja .env.example).")
    agent = Agent(
        model,
        deps_type=Session,
        system_prompt=SYSTEM_PROMPT,
        instructions=_focused_case_instructions,
        tools=AGENT_TOOLS,
        model_settings=_model_settings(),
    )
    agent.output_validator(_require_cited_cases_queried)
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


def _model_settings() -> ModelSettings | None:
    thinking = os.environ.get(THINKING_VARIABLE, "").strip().lower()
    if not thinking:
        return None
    return {"thinking": BOOLEAN_SETTINGS.get(thinking, thinking)}


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
            reason = _temporary_failure_reason(error)
            if reason is None or attempt == MAX_ATTEMPTS:
                raise
            wait = RETRY_WAIT_SECONDS * attempt
            on_retry(
                f"O serviço do modelo está indisponível no momento ({reason}). "
                f"Tentando de novo em {wait} s… (tentativa {attempt + 1} de {MAX_ATTEMPTS})"
            )
            sleep(wait)
    raise AssertionError("inalcançável: a última tentativa devolve ou relança")


def _temporary_failure_reason(error: ModelAPIError) -> str | None:
    """Motivo legível se a falha for temporária (vale a pena repetir); None se não for (chave inválida, pedido errado)."""
    if not isinstance(error, ModelHTTPError):
        return "sem conexão com o modelo"
    if error.status_code not in TEMPORARY_HTTP_STATUSES:
        return None
    detail = TEMPORARY_HTTP_STATUSES[error.status_code]
    return f"erro {error.status_code}, {detail}" if detail else f"erro {error.status_code}"
