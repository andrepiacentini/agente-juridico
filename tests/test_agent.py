"""Criação do agente: modelo e raciocínio vêm da configuração, sem caminho especial por fornecedor. Sem IA real."""

import pytest
from pydantic_ai.messages import SystemPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from case_assistant.agent import ModelNotConfiguredError, ModelOption, build_agent, model_options
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


EXPECTED_TOOLS = {
    "find_case", "list_parties", "list_movements", "list_documents", "read_document",
    "search_text", "search_parties", "search_cases", "run_sql", "prepare_draft",
}


def test_agent_registers_every_tool_and_each_one_runs(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    agent = build_agent(TestModel(call_tools="all"))  # chama toda ferramenta com argumentos gerados

    with open_session() as session:
        result = agent.run_sync("teste", deps=session)

    parts = [part for message in result.all_messages() for part in message.parts]
    called = {part.tool_name for part in parts if isinstance(part, ToolCallPart)}
    returned = {part.tool_name: part.content for part in parts if isinstance(part, ToolReturnPart)}
    assert called == EXPECTED_TOOLS
    assert set(returned) == EXPECTED_TOOLS
    assert all(isinstance(content, dict) for content in returned.values())


def test_every_tool_runs_in_the_conversation_thread() -> None:
    import inspect

    from case_assistant.agent_tools import AGENT_TOOLS

    # ferramentas síncronas iriam para outras threads, e a conexão SQLite só funciona na thread que a criou
    assert all(inspect.iscoroutinefunction(tool) for tool in AGENT_TOOLS)


def test_every_tool_tells_the_model_when_to_use_it_and_what_each_argument_is() -> None:
    from case_assistant.agent_tools import AGENT_TOOLS
    import inspect

    for tool in AGENT_TOOLS:
        docstring = inspect.getdoc(tool)
        parameters = [name for name in inspect.signature(tool).parameters if name != "ctx"]
        assert docstring and len(docstring.splitlines()[0]) <= 120, tool.__name__
        assert all(f"{name}:" in docstring for name in parameters), tool.__name__


def test_tools_use_the_connection_of_the_session(monkeypatch) -> None:
    monkeypatch.delenv("LLM_THINKING", raising=False)
    agent = build_agent(TestModel(call_tools=["find_case"]))

    with open_session() as session:
        result = agent.run_sync("teste", deps=session)

    returns = [part.content for m in result.all_messages() for part in m.parts if isinstance(part, ToolReturnPart)]
    assert returns and returns[0]["found"] is False  # o número gerado não existe, mas a consulta rodou no banco da sessão


LOCAL_MODEL = "ollama:qwen3:4b-instruct-2507-q4_K_M"
CLOUD_MODEL = "google:gemini-3.8-flash"


def test_model_options_come_from_the_configuration_with_the_thinking_of_each_one(monkeypatch) -> None:
    # T10.3 (D69): a lista do seletor da tela vem do .env; o código não tem nome de modelo.
    monkeypatch.setenv("LLM_MODEL", LOCAL_MODEL)
    monkeypatch.setenv("LLM_MODEL_OPTIONS", f"{LOCAL_MODEL}, {CLOUD_MODEL}@low")

    assert model_options() == [ModelOption(LOCAL_MODEL, ""), ModelOption(CLOUD_MODEL, "low")]


def test_the_configured_model_is_always_the_first_option(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", CLOUD_MODEL)
    monkeypatch.setenv("LLM_THINKING", "low")
    monkeypatch.setenv("LLM_MODEL_OPTIONS", LOCAL_MODEL)

    assert model_options() == [ModelOption(CLOUD_MODEL, "low"), ModelOption(LOCAL_MODEL, "")]


def test_without_options_the_list_has_only_the_configured_model(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", LOCAL_MODEL)
    monkeypatch.delenv("LLM_MODEL_OPTIONS", raising=False)
    monkeypatch.delenv("LLM_THINKING", raising=False)

    assert model_options() == [ModelOption(LOCAL_MODEL, "")]


def test_an_explicit_thinking_wins_over_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("LLM_THINKING", "low")

    assert build_agent(TestModel(), thinking="").model_settings is None
    assert build_agent(TestModel(), thinking="high").model_settings == {"thinking": "high"}
