"""Ferramentas como o modelo as vê: cada uma pega a conexão da sessão e chama a ferramenta do banco (T5.4).

As docstrings são o texto que o modelo lê para decidir qual ferramenta usar: primeira linha = quando usar,
`Args` = o que cada parâmetro espera. As ferramentas de verdade ficam em `tools.py` e `sql_query.py`.

São `async` de propósito: o Pydantic AI roda ferramentas síncronas em outras threads, e a conexão SQLite só pode
ser usada pela thread que a criou. Assim, elas rodam na thread da conversa, uma de cada vez — nunca duas usando a
conexão ao mesmo tempo, o que importa porque `run_sql` liga o autorizador e o cronômetro durante a consulta.
As consultas levam milissegundos, então não há ganho em paralelizá-las.
"""

from collections.abc import Callable
from typing import Any

from pydantic_ai import RunContext

from case_assistant import sql_query, tools
from case_assistant.prompts import DRAFT_INSTRUCTIONS
from case_assistant.session import Session


MISSING_CASE_NUMBER_MESSAGE = "Informe o número do processo: nenhum processo foi consultado nesta conversa."
MAX_FAILED_SQL_ATTEMPTS = 2
SQL_ATTEMPT_LIMIT_MESSAGE = (
    f"Limite de tentativas atingido: as {MAX_FAILED_SQL_ATTEMPTS} últimas consultas SQL falharam. "
    "Não tente de novo; informe ao usuário que não foi possível obter a resposta com uma consulta ao banco."
)


def _run_case_tool(
    ctx: RunContext[Session], tool: Callable[..., dict[str, Any]], case_number: str | None
) -> dict[str, Any]:
    """Sem número, usa o processo em foco (T6.3); o processo encontrado vira o novo foco (T6.1).

    Buscas de vários processos não passam por aqui e, por isso, não mudam o foco.
    """
    case_number = case_number or ctx.deps.focused_case_number
    if case_number is None:
        return {"found": False, "message": MISSING_CASE_NUMBER_MESSAGE}
    result = tool(ctx.deps.connection, case_number)
    if result.get("found"):
        ctx.deps.focused_case_number = result["case_number"]
    return result


async def find_case(ctx: RunContext[Session], case_number: str | None = None) -> dict[str, Any]:
    """Cartão do processo: classe, assunto, vara, juiz, datas, valor, situação, julgamento e avisos. Comece por ela.

    Args:
        case_number: número do processo no padrão CNJ, como 0000007-79.2023.8.99.9014; se omitido, usa o processo em foco.
    """
    return _run_case_tool(ctx, tools.find_case, case_number)


async def list_parties(ctx: RunContext[Session], case_number: str | None = None) -> dict[str, Any]:
    """Partes do processo por polo (autores e réus), com pessoa física/jurídica e CPF/CNPJ.

    Args:
        case_number: número do processo no padrão CNJ; se omitido, usa o processo em foco.
    """
    return _run_case_tool(ctx, tools.list_parties, case_number)


async def list_movements(ctx: RunContext[Session], case_number: str | None = None) -> dict[str, Any]:
    """Andamento do processo em ordem de data. Use para resumir, inclusive processos sem documentos.

    Args:
        case_number: número do processo no padrão CNJ; se omitido, usa o processo em foco.
    """
    return _run_case_tool(ctx, tools.list_movements, case_number)


async def list_documents(ctx: RunContext[Session], case_number: str | None = None) -> dict[str, Any]:
    """Índice dos documentos do processo (sem texto), com os advogados e o lado de cada um.

    Args:
        case_number: número do processo no padrão CNJ; se omitido, usa o processo em foco.
    """
    return _run_case_tool(ctx, tools.list_documents, case_number)


async def read_document(ctx: RunContext[Session], document_id: int) -> dict[str, Any]:
    """Texto completo de um documento, com tipo e data para citar. Leia só os documentos necessários.

    Args:
        document_id: id do documento, obtido em list_documents.
    """
    return tools.read_document(ctx.deps.connection, document_id)


async def search_text(
    ctx: RunContext[Session],
    term: str,
    case_number: str | None = None,
    document_type: str | None = None,
    limit: int = tools.SEARCH_DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Documentos que mencionam um termo ou expressão, com um trecho em volta.

    Args:
        term: palavra ou expressão a procurar, como "inversão do ônus da prova".
        case_number: opcional; limita a busca a um processo.
        document_type: opcional; limita a um tipo de documento, como "Sentença".
        limit: quantos resultados trazer (máximo 20).
    """
    return tools.search_text(ctx.deps.connection, term, case_number, document_type, limit)


async def search_parties(ctx: RunContext[Session], name: str) -> dict[str, Any]:
    """Pessoas pelo nome, separadas por CPF/CNPJ, com os processos de cada uma. Detecta homônimos.

    Args:
        name: nome ou parte do nome da pessoa ou empresa.
    """
    return tools.search_parties(ctx.deps.connection, name)


async def search_cases(
    ctx: RunContext[Session],
    subject: str | None = None,
    case_class: str | None = None,
    district: str | None = None,
    court_unit: str | None = None,
    judge: str | None = None,
    status: str | None = None,
    filing_date_from: str | None = None,
    filing_date_to: str | None = None,
    sentence_date_from: str | None = None,
    sentence_date_to: str | None = None,
    claim_value_min: float | None = None,
    claim_value_max: float | None = None,
    order_by: str = "filing_date",
    limit: int = tools.SEARCH_CASES_DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Processos por característica — "quais/quantos processos…" —, com o total e uma lista.

    Args:
        subject: assunto, ou parte dele, como "plano de saúde".
        case_class: classe processual, como "execução fiscal".
        district: comarca, como "Joinville".
        court_unit: vara, como "1ª Vara Cível".
        judge: nome do magistrado, ou parte dele.
        status: situação: "julgado", "em andamento", "arquivado" ou "suspenso".
        filing_date_from: autuação a partir desta data, AAAA-MM-DD.
        filing_date_to: autuação até esta data, AAAA-MM-DD.
        sentence_date_from: sentença a partir desta data, AAAA-MM-DD.
        sentence_date_to: sentença até esta data, AAAA-MM-DD.
        claim_value_min: valor da causa mínimo, em reais.
        claim_value_max: valor da causa máximo, em reais.
        order_by: "filing_date", "sentence_date" ou "claim_value" (maior primeiro).
        limit: quantos processos listar (máximo 50).
    """
    return tools.search_cases(
        ctx.deps.connection, subject, case_class, district, court_unit, judge, status,
        filing_date_from, filing_date_to, sentence_date_from, sentence_date_to,
        claim_value_min, claim_value_max, order_by, limit,
    )


async def run_sql(ctx: RunContext[Session], sql: str) -> dict[str, Any]:
    """Consulta SQL de leitura (SELECT ou WITH) no banco. Use só quando nenhuma outra ferramenta servir.

    Args:
        sql: um único comando SELECT ou WITH, seguindo a descrição do banco nas instruções.
    """
    session = ctx.deps
    _restart_sql_attempts_on_new_question(session, ctx.run_id)
    if session.failed_sql_attempts >= MAX_FAILED_SQL_ATTEMPTS:
        return {"found": False, "message": SQL_ATTEMPT_LIMIT_MESSAGE}
    result = sql_query.run_sql(session.connection, sql)
    session.failed_sql_attempts = 0 if result["found"] else session.failed_sql_attempts + 1
    return result


def _restart_sql_attempts_on_new_question(session: Session, run_id: str) -> None:
    # Cada pergunta é uma execução do agente (run_id próprio). Contar na conversa inteira travaria o run_sql
    # para sempre depois de dois erros: bloqueado, ele nunca mais acertaria para zerar a contagem.
    if session.sql_attempts_run_id != run_id:
        session.sql_attempts_run_id = run_id
        session.failed_sql_attempts = 0


async def prepare_draft(ctx: RunContext[Session], case_number: str | None = None) -> dict[str, Any]:
    """Para minuta de sentença: confere se há base, lista as peças a ler e diz como redigir. Chame antes de escrever.

    Args:
        case_number: número do processo no padrão CNJ; se omitido, usa o processo em foco.
    """
    result = _run_case_tool(ctx, tools.prepare_draft, case_number)
    if result.get("ready"):
        result["instructions"] = DRAFT_INSTRUCTIONS
    return result


AGENT_TOOLS = (
    find_case, list_parties, list_movements, list_documents, read_document,
    search_text, search_parties, search_cases, run_sql, prepare_draft,
)
