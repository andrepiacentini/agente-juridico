"""Laço do agente com Pydantic AI: modelo escolhido por `LLM_MODEL`, ferramentas e estado da sessão (E05, E06)."""

import os

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings

from case_assistant.prompts import SYSTEM_PROMPT
from case_assistant.session import Session

MODEL_VARIABLE = "LLM_MODEL"
# Opcional: nível de raciocínio ("low", "true", "false"…). O Gemini precisa de "low" (D30); o modelo local, de nada.
THINKING_VARIABLE = "LLM_THINKING"
BOOLEAN_SETTINGS = {"true": True, "false": False}


class ModelNotConfiguredError(RuntimeError):
    """Nenhum modelo foi informado em LLM_MODEL."""


def build_agent(model: Model | str | None = None) -> Agent[Session, str]:
    """Cria o agente. O modelo e o raciocínio vêm da configuração: o código não tem caminho especial por fornecedor."""
    model = model or os.environ.get(MODEL_VARIABLE)
    if not model:
        raise ModelNotConfiguredError(f"Defina {MODEL_VARIABLE} no .env (veja .env.example).")
    return Agent(model, deps_type=Session, system_prompt=SYSTEM_PROMPT, model_settings=_model_settings())


def _model_settings() -> ModelSettings | None:
    thinking = os.environ.get(THINKING_VARIABLE, "").strip().lower()
    if not thinking:
        return None
    return {"thinking": BOOLEAN_SETTINGS.get(thinking, thinking)}
