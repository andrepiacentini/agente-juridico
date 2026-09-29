"""Como uma chamada de ferramenta aparece para quem usa, no terminal e na web: o agente decidindo, à vista (T10.2)."""

import json
from typing import Any

from pydantic_ai.messages import ToolCallPart


def tool_call_label(part: ToolCallPart) -> str:
    """A ferramenta com os argumentos que o modelo escolheu: find_case(case_number='0000007-79.2023.8.99.9014')."""
    arguments = ", ".join(f"{name}={value!r}" for name, value in part.args_as_dict().items())
    return f"{part.tool_name}({arguments})"


def tool_result_text(content: Any) -> str:
    """O que a ferramenta devolveu, em JSON legível e com acentos; texto simples fica como está."""
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, indent=2, default=str)
