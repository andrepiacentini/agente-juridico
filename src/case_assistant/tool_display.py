"""Como uma chamada de ferramenta aparece para quem usa, no terminal e na web: o agente decidindo, à vista (T10.2)."""

import json
from typing import Any

from pydantic_ai.messages import (
    AgentStreamEvent, FunctionToolCallEvent, FunctionToolResultEvent, PartStartEvent, TextPart, ThinkingPart, ToolCallPart,
)

# Fases da resposta (T14.9): o modelo local passa ~30 s escrevendo depois da última ferramenta, e sem um sinal na
# tela a espera parecia travamento. Cada nome é a frase inteira que o usuário lê enquanto o passo pisca.
STARTING_PHASE = "Lendo a pergunta…"
THINKING_PHASE = "Pensando…"
QUERYING_PHASE = "Consultando o banco de dados…"
ANALYZING_PHASE = "Analisando o que encontrou…"
WRITING_PHASE = "Escrevendo a resposta…"
QUERIED_DATABASE = "Consultou o banco de dados"
ANSWERED_FROM_CONVERSATION = "Respondeu com o que já estava na conversa"


def tool_call_label(part: ToolCallPart) -> str:
    """A ferramenta com os argumentos que o modelo escolheu: find_case(case_number='0000007-79.2023.8.99.9014')."""
    arguments = ", ".join(f"{name}={value!r}" for name, value in part.args_as_dict().items())
    return f"{part.tool_name}({arguments})"


def tool_result_text(content: Any) -> str:
    """O que a ferramenta devolveu, em JSON legível e com acentos; texto simples fica como está."""
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, indent=2, default=str)


def answer_phase(event: AgentStreamEvent) -> str | None:
    """A fase que o evento do agente inicia; None se ele não muda o que o usuário vê."""
    if isinstance(event, FunctionToolCallEvent):
        return QUERYING_PHASE
    if isinstance(event, FunctionToolResultEvent):
        return ANALYZING_PHASE
    if isinstance(event, PartStartEvent) and isinstance(event.part, ThinkingPart):
        return THINKING_PHASE
    if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
        return WRITING_PHASE
    return None


def finished_label(tools_called: bool) -> str:
    """Como o bloco de passos fica depois da resposta: com consulta ao banco ou só com o histórico da conversa."""
    return QUERIED_DATABASE if tools_called else ANSWERED_FROM_CONVERSATION
