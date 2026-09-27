"""Laço do agente com Pydantic AI: modelo escolhido por `LLM_MODEL`, ferramentas e estado da sessão (E05, E06)."""

import os
import time
from collections.abc import Callable
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings

from case_assistant.agent_tools import AGENT_TOOLS
from case_assistant.prompts import SYSTEM_PROMPT
from case_assistant.session import Session

MODEL_VARIABLE = "LLM_MODEL"
# Opcional: nível de raciocínio ("low", "true", "false"…). O Gemini precisa de "low" (D30); o modelo local, de nada.
THINKING_VARIABLE = "LLM_THINKING"
BOOLEAN_SETTINGS = {"true": True, "false": False}
# Recusas temporárias do serviço do modelo (D41): tentar de novo, avisando o usuário, antes de desistir.
MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 5  # 5 s antes da 2ª tentativa, 10 s antes da 3ª
TEMPORARY_HTTP_STATUSES = {429: "limite de pedidos", 500: "", 502: "", 503: "", 504: ""}


class ModelNotConfiguredError(RuntimeError):
    """Nenhum modelo foi informado em LLM_MODEL."""


def build_agent(model: Model | str | None = None) -> Agent[Session, str]:
    """Cria o agente. O modelo e o raciocínio vêm da configuração: o código não tem caminho especial por fornecedor."""
    model = model or os.environ.get(MODEL_VARIABLE)
    if not model:
        raise ModelNotConfiguredError(f"Defina {MODEL_VARIABLE} no .env (veja .env.example).")
    return Agent(
        model, deps_type=Session, system_prompt=SYSTEM_PROMPT, tools=AGENT_TOOLS, model_settings=_model_settings()
    )


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
