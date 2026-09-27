"""Criação do agente: modelo e raciocínio vêm da configuração, sem caminho especial por fornecedor. Sem IA real."""

import pytest
from pydantic_ai.messages import SystemPromptPart
from pydantic_ai.models.test import TestModel

from case_assistant.agent import ModelNotConfiguredError, build_agent
from case_assistant.prompts import SYSTEM_PROMPT
from case_assistant.session import open_session


def test_agent_answers_with_the_system_prompt_and_the_session(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    agent = build_agent(TestModel(custom_output_text="Olá! Como posso ajudar?"))

    with open_session() as session:
        result = agent.run_sync("olá", deps=session)

    assert result.output == "Olá! Como posso ajudar?"
    system_parts = [part for message in result.all_messages() for part in message.parts if isinstance(part, SystemPromptPart)]
    assert [part.content for part in system_parts] == [SYSTEM_PROMPT]


def test_model_comes_from_llm_model_variable(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "test")

    assert build_agent().model.model_name == "test"


def test_missing_llm_model_is_a_clear_error(monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)

    with pytest.raises(ModelNotConfiguredError, match="LLM_MODEL"):
        build_agent()


@pytest.mark.parametrize(("configured", "expected"), [("low", "low"), ("false", False), ("true", True)])
def test_thinking_comes_from_llm_thinking_variable(monkeypatch, configured: str, expected) -> None:
    monkeypatch.setenv("LLM_THINKING", configured)

    assert build_agent(TestModel()).model_settings == {"thinking": expected}


def test_without_llm_thinking_the_model_keeps_its_default(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)

    assert build_agent(TestModel()).model_settings is None
