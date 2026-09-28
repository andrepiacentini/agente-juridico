"""Ferramentas que o agente chama para consultar o banco; devolvem metadados e só leem texto sob demanda (E03, E04)."""

import functools
import re
import sqlite3
from collections.abc import Callable
from typing import Any

from case_assistant.case_number import check_digits, extract_case_number, extract_case_numbers, has_valid_check_digits
from case_assistant.citations import REGISTRY_SOURCE, brazilian_date, document_source, movement_source
from case_assistant.db import ensure_search_index
from case_assistant.text_normalization import comparable_district, comparable_text

# LEFT JOIN: 1.044 processos não têm magistrado e não podem sumir da consulta.
# LOWER(TRIM()): a situação vem como "Julgado", "JULGADO" ou "julgado" e é devolvida sempre em minúsculas.
FIND_CASE_QUERY = """
    SELECT p.id, p.numero, p.classe, p.assunto, p.comarca, p.dt_aut, p.data_sentenca, p.valor_causa,
           LOWER(TRIM(p.situacao)) AS situacao,
           u.vara, u.comarca AS unidade_comarca, u.status AS unidade_status,
           m.nome AS magistrado_nome, m.situacao AS magistrado_situacao,
           (SELECT COUNT(*) FROM documento WHERE processo_id = p.id) AS total_documentos,
           (SELECT COUNT(*) FROM movimentacao WHERE processo_id = p.id) AS total_movimentacoes
    FROM processo p
    LEFT JOIN unidade u ON u.id = p.unidade_id
    LEFT JOIN magistrado m ON m.id = p.magistrado_id
    WHERE p.id = ?
"""


# Julgamento nunca vem de um sinal só: 4.426 processos têm data de sentença sem o texto da sentença.
SENTENCE_MOVEMENT_CODES = (9219, 9220, 9221)
SENTENCE_DOCUMENT_TYPES = ("Sentença", "Sentença Homologatória de Acordo")
SENTENCE_MOVEMENT_QUERY = f"""
    SELECT codigo, descricao, data_mov FROM movimentacao
    WHERE processo_id = ? AND codigo IN ({", ".join("?" * len(SENTENCE_MOVEMENT_CODES))})
    ORDER BY data_mov DESC LIMIT 1
"""
SENTENCE_DOCUMENT_QUERY = f"""
    SELECT id, tipo, dt_juntada FROM documento
    WHERE processo_id = ? AND tipo IN ({", ".join("?" * len(SENTENCE_DOCUMENT_TYPES))})
    ORDER BY dt_juntada DESC LIMIT 1
"""


# Agrupa por parte: 99 vínculos repetem a mesma parte no mesmo polo do mesmo processo.
LIST_PARTIES_QUERY = """
    SELECT pp.polo, pa.nome, pa.documento, COUNT(*) AS vinculos
    FROM processo_parte pp JOIN parte pa ON pa.id = pp.parte_id
    WHERE pp.processo_id = ?
    GROUP BY pp.polo, pa.id
    ORDER BY pa.nome
"""
# Desempate por id: 2.960 vezes um processo tem mais de uma movimentação no mesmo dia.
LIST_MOVEMENTS_QUERY = """
    SELECT data_mov, codigo, descricao FROM movimentacao
    WHERE processo_id = ?
    ORDER BY data_mov, id
"""
FINAL_JUDGMENT_CODE = 9848  # Trânsito em Julgado
APPEAL_CODE = 9246  # Recurso de Apelação Interposto
# O texto só é lido aqui para conferir a assinatura; nunca volta na resposta (metadados primeiro, D05).
LIST_DOCUMENTS_QUERY = """
    SELECT id, tipo, autor, dt_juntada, num_paginas, texto FROM documento
    WHERE processo_id = ?
    ORDER BY dt_juntada, id
"""
OAB_PATTERN = re.compile(r"OAB/([A-Z]{2})\s*([\d.]+)")
# Peças que só um dos lados apresenta; as demais herdam o lado pela OAB de quem assinou.
SIDE_BY_ANCHOR_DOCUMENT_TYPE = {
    "Petição Inicial": "autor",
    "Réplica": "autor",
    "Emenda à Inicial": "autor",
    "Contestação": "réu",
    "Exceção de Pré-Executividade": "réu",
    "Embargos à Execução Fiscal": "réu",
}
READ_DOCUMENT_QUERY = """
    SELECT d.id, d.tipo, d.autor, d.dt_juntada, d.num_paginas, d.texto, p.numero
    FROM documento d JOIN processo p ON p.id = d.processo_id
    WHERE d.id = ?
"""
SEARCH_DEFAULT_LIMIT, SEARCH_MAX_LIMIT = 10, 20
SEARCH_TEXT_QUERY = """
    SELECT d.id, d.tipo, d.dt_juntada, p.numero,
           snippet(document_search, 0, '[', ']', '…', 12) AS trecho
    FROM temp.document_search
    JOIN documento d ON d.id = document_search.rowid
    JOIN processo p ON p.id = d.processo_id
    WHERE document_search MATCH :query
      AND (:case_id IS NULL OR d.processo_id = :case_id)
      AND (:document_type IS NULL OR d.tipo = :document_type)
    ORDER BY rank
    LIMIT :limit
"""
SEARCH_TEXT_COUNT_QUERY = """
    SELECT COUNT(*) AS total
    FROM temp.document_search
    JOIN documento d ON d.id = document_search.rowid
    WHERE document_search MATCH :query
      AND (:case_id IS NULL OR d.processo_id = :case_id)
      AND (:document_type IS NULL OR d.tipo = :document_type)
"""
WORD_PATTERN = re.compile(r"\w+")
SEARCH_PARTIES_MAX_PEOPLE, SEARCH_PARTIES_MAX_CASES = 10, 10
SEARCH_CASES_DEFAULT_LIMIT, SEARCH_CASES_MAX_LIMIT = 20, 50
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
SEARCH_CASES_ORDER_COLUMNS = {"filing_date": "p.dt_aut", "sentence_date": "p.data_sentenca", "claim_value": "p.valor_causa"}
# LEFT JOIN: 1.044 processos não têm magistrado. Textos comparados sem acento/caixa (funções registradas em db.py).
SEARCH_CASES_FROM = """
    FROM processo p
    LEFT JOIN unidade u ON u.id = p.unidade_id
    LEFT JOIN magistrado m ON m.id = p.magistrado_id
"""
# Busca vazia não quer dizer que o dado não existe (D52, T7.9): cada filtro de texto é conferido sozinho.
# Listas curtas vão na mensagem para o modelo escolher um valor que existe; comarca (230) e magistrado (200), não.
SEARCH_CASES_FILTER_VALUES_QUERIES = {
    "classe": ("Classes", "SELECT DISTINCT classe FROM processo ORDER BY classe"),
    "assunto": ("Assuntos", "SELECT DISTINCT assunto FROM processo ORDER BY assunto"),
    "vara": ("Varas", "SELECT DISTINCT vara FROM unidade ORDER BY vara"),
    "situação": ("Situações", "SELECT DISTINCT LOWER(TRIM(situacao)) FROM processo ORDER BY 1"),
    "comarca": None,
    "magistrado": None,
}
MATCHING_PARTY_DOCUMENTS_QUERY = """
    SELECT DISTINCT pa.documento FROM temp.party_search
    JOIN parte pa ON pa.id = party_search.rowid
    WHERE party_search MATCH ?
"""
# A pessoa é o CPF/CNPJ: 643 nomes são homônimos com documentos diferentes,
# e 332 documentos aparecem no cadastro com mais de um nome.
PARTY_CASES_QUERY = """
    SELECT pa.documento, pa.nome, p.numero, pp.polo
    FROM parte pa
    JOIN processo_parte pp ON pp.parte_id = pa.id
    JOIN processo p ON p.id = pp.processo_id
    WHERE pa.documento IN ({placeholders})
    ORDER BY p.numero
"""
CPF_LENGTH, CNPJ_LENGTH = 14, 18  # "999.539.988-87" e "99.193.997/0001-35"
INACTIVE_JUDGE_STATUSES = ("aposentado", "removido")
ACTIVE_UNIT_STATUS = "ativa"
# Acima disso só existe um valor no banco: 9.999.999.999, com cara de preenchimento; o seguinte é 1,27 milhão.
IMPLAUSIBLE_CLAIM_VALUE = 100_000_000
STATUSES_WITHOUT_SENTENCE = ("em andamento", "suspenso")
ROLE_BY_POLE = {"ativo": "autor", "passivo": "réu"}
# Sem o pedido do autor e a defesa do réu não há base para propor uma decisão (edital; plan.md §7).
# 1.586 processos têm as duas peças; 2.105 só a petição inicial; nenhum só a contestação.
DRAFT_REQUIRED_DOCUMENT_TYPES = ("Petição Inicial", "Contestação")
DRAFT_BASIS_QUERY = f"""
    SELECT DISTINCT tipo FROM documento
    WHERE processo_id = ? AND tipo IN ({", ".join("?" * len(DRAFT_REQUIRED_DOCUMENT_TYPES))})
"""


class NotFoundError(Exception):
    """O que a ferramenta procurou não existe no banco."""


class CaseNotFoundError(NotFoundError):
    """O texto não traz um número de processo no padrão CNJ, ou o processo não está no banco."""


class DocumentNotFoundError(NotFoundError):
    """Não há documento com o id pedido."""


def _reports_not_found(tool: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    """Fronteira da ferramenta: "não encontrado" vira resposta para o agente, não erro."""

    @functools.wraps(tool)
    def tool_with_not_found_answer(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return tool(*args, **kwargs)
        except NotFoundError as error:
            return {"found": False, "message": str(error)}

    return tool_with_not_found_answer


def _resolve_case_id(connection: sqlite3.Connection, case_number: str) -> int:
    normalized_number = extract_case_number(case_number)
    if normalized_number is None:
        raise CaseNotFoundError(f"Não reconheci um número de processo no padrão CNJ em '{case_number}'.")
    row = connection.execute("SELECT id FROM processo WHERE numero = ?", (normalized_number,)).fetchone()
    if row is None:
        raise CaseNotFoundError(_case_not_found_message(normalized_number))
    return row["id"]


def _case_not_found_message(case_number: str) -> str:
    """Separa "você digitou errado" de "esse processo não existe" pelo dígito verificador (T7.8)."""
    message = f"Processo {case_number} não encontrado no banco."
    if has_valid_check_digits(case_number):
        return message
    return (
        f"{message} O dígito verificador ({check_digits(case_number)}) não confere com o restante do número: "
        "provavelmente houve erro de digitação. Confira o número do processo."
    )


@_reports_not_found
def find_case(connection: sqlite3.Connection, case_number: str) -> dict[str, Any]:
    """Cartão de identificação do processo: classe, assunto, vara, magistrado, datas, valor e totais."""
    row = connection.execute(FIND_CASE_QUERY, (_resolve_case_id(connection, case_number),)).fetchone()
    case = {
        "found": True,
        "case_number": row["numero"],
        "case_class": row["classe"],
        "subject": row["assunto"],
        "district": row["comarca"],
        "court_unit": row["vara"],
        "court_unit_district": row["unidade_comarca"],
        "court_unit_status": row["unidade_status"],
        "judge": _judge(row),
        "filing_date": brazilian_date(row["dt_aut"]),
        "sentence_date": brazilian_date(row["data_sentenca"]),
        "claim_value": row["valor_causa"],
        "status": row["situacao"],
        "document_count": row["total_documentos"],
        "movement_count": row["total_movimentacoes"],
        "judgment": _judgment(connection, row["id"], row["data_sentenca"]),
    }
    case["warnings"] = _registry_warnings(case)
    case["source"] = REGISTRY_SOURCE
    return case


def _registry_warnings(case: dict[str, Any]) -> list[str]:
    """Inconsistências do cadastro, reportadas como estão — nunca corrigidas nem resolvidas pela ferramenta."""
    warnings = []
    judge = case["judge"]
    if judge is None:
        warnings.append("Processo sem magistrado cadastrado.")
    elif judge["status"] in INACTIVE_JUDGE_STATUSES:
        warnings.append(f"Magistrado {judge['name']} está {judge['status']}.")

    if case["court_unit_status"] != ACTIVE_UNIT_STATUS:
        warnings.append(f"A unidade '{case['court_unit']}' ({case['court_unit_district']}) está {case['court_unit_status']}.")

    district, unit_district = case["district"], case["court_unit_district"]
    if district != unit_district:
        if comparable_district(district) == comparable_district(unit_district):
            warnings.append(
                f"A comarca está grafada de forma diferente no processo ('{district}') e na vara ('{unit_district}')."
            )
        else:
            warnings.append(f"Comarca do processo ('{district}') difere da comarca da vara ('{unit_district}').")

    claim_value = case["claim_value"]
    if claim_value is None:
        warnings.append("Valor da causa não informado.")
    elif claim_value <= 0:
        warnings.append(f"Valor da causa inválido ({_brazilian_currency(claim_value)}).")
    elif claim_value >= IMPLAUSIBLE_CLAIM_VALUE:
        warnings.append(f"Valor da causa implausível ({_brazilian_currency(claim_value)}): parece valor de preenchimento.")

    status, sentence_date = case["status"], case["sentence_date"]
    if status == "julgado" and sentence_date is None:
        warnings.append("Situação 'julgado' sem data de sentença.")
    elif status in STATUSES_WITHOUT_SENTENCE and sentence_date is not None:
        warnings.append(f"Situação '{status}' com data de sentença ({sentence_date}).")
    return warnings


def _brazilian_currency(value: float) -> str:
    return "R$ " + f"{value:,.2f}".replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")





def _judgment(connection: sqlite3.Connection, case_id: int, sentence_date: str | None) -> dict[str, Any]:
    """Cruza data de sentença, movimentação de sentença e documento de sentença, sem escolher um lado."""
    movement = connection.execute(SENTENCE_MOVEMENT_QUERY, (case_id, *SENTENCE_MOVEMENT_CODES)).fetchone()
    document = connection.execute(SENTENCE_DOCUMENT_QUERY, (case_id, *SENTENCE_DOCUMENT_TYPES)).fetchone()
    signals = {
        "data de sentença": sentence_date is not None,
        "movimentação de sentença": movement is not None,
        "documento de sentença": document is not None,
    }
    return {
        "summary": _judgment_summary(signals),
        "sentence_movement": _movement_card(movement),
        "sentence_document": _document_card(document),
    }


def _movement_card(movement: sqlite3.Row | None) -> dict[str, Any] | None:
    if movement is None:
        return None
    return _movement(movement["codigo"], movement["descricao"], movement["data_mov"])


def _document_card(document: sqlite3.Row | None) -> dict[str, Any] | None:
    if document is None:
        return None
    return {
        "id": document["id"],
        "type": document["tipo"],
        "date": brazilian_date(document["dt_juntada"]),
        "source": document_source(document["id"], document["tipo"], document["dt_juntada"]),
    }


def _movement(code: int, description: str, iso_date: str) -> dict[str, Any]:
    return {
        "code": code,
        "description": description,
        "date": brazilian_date(iso_date),
        "source": movement_source(code, description, iso_date),
    }


def _judgment_summary(signals: dict[str, bool]) -> str:
    present = [name for name, found in signals.items() if found]
    absent = [name for name, found in signals.items() if not found]
    if not absent:
        return "Julgado: data de sentença, movimentação de sentença e documento de sentença conferem."
    if not present:
        return "Não há sinal de sentença: sem data, sem movimentação e sem documento de sentença."
    missing_text_note = " (o texto da sentença não está no banco)" if "documento de sentença" in absent else ""
    return (
        f"Sinais divergentes. Presentes: {', '.join(present)}. "
        f"{'Ausente' if len(absent) == 1 else 'Ausentes'}: {', '.join(absent)}{missing_text_note}."
    )


def _judge(row: sqlite3.Row) -> dict[str, str] | None:
    if row["magistrado_nome"] is None:
        return None
    return {"name": row["magistrado_nome"], "status": row["magistrado_situacao"]}


@_reports_not_found
def list_parties(connection: sqlite3.Connection, case_number: str) -> dict[str, Any]:
    """Partes do processo por polo (ativo = autores, passivo = réus), com pessoa física/jurídica e CPF/CNPJ."""
    rows = connection.execute(LIST_PARTIES_QUERY, (_resolve_case_id(connection, case_number),)).fetchall()
    return {
        "found": True,
        "case_number": extract_case_number(case_number),
        "plaintiffs": [_party_card(row) for row in rows if row["polo"] == "ativo"],
        "defendants": [_party_card(row) for row in rows if row["polo"] == "passivo"],
        "warnings": [
            f"{row['nome']} aparece mais de uma vez no polo {row['polo']} do cadastro." for row in rows if row["vinculos"] > 1
        ],
        "source": REGISTRY_SOURCE,
    }


@_reports_not_found
def list_movements(connection: sqlite3.Connection, case_number: str) -> dict[str, Any]:
    """Andamento do processo em ordem de data: cada movimentação já no formato de citação (código, descrição, data)."""
    rows = connection.execute(LIST_MOVEMENTS_QUERY, (_resolve_case_id(connection, case_number),)).fetchall()
    return {
        "found": True,
        "case_number": extract_case_number(case_number),
        "movements": [movement_source(row["codigo"], row["descricao"], row["data_mov"]) for row in rows],
        "warnings": _timeline_warnings(rows),
    }


def _timeline_warnings(rows: list[sqlite3.Row]) -> list[str]:
    """Sequências incomuns no andamento, reportadas para conferência humana — podem ser exceções legítimas."""
    final_judgment_dates = [row["data_mov"] for row in rows if row["codigo"] == FINAL_JUDGMENT_CODE]
    if not final_judgment_dates:
        return []
    final_judgment_date = min(final_judgment_dates)
    warnings = [
        f"Recurso de apelação registrado em {brazilian_date(row['data_mov'])}, "
        f"depois do trânsito em julgado ({brazilian_date(final_judgment_date)}). "
        "Sequência incomum, que merece conferência: pode ser recurso interposto fora do prazo ou erro de cadastro."
        for row in rows
        if row["codigo"] == APPEAL_CODE and row["data_mov"] > final_judgment_date
    ]
    if not any(row["codigo"] in SENTENCE_MOVEMENT_CODES for row in rows):
        warnings.append(
            f"Trânsito em julgado ({brazilian_date(final_judgment_date)}) sem movimentação de sentença no andamento. "
            "Merece conferência: a sentença pode não ter sido registrada."
        )
    return warnings


@_reports_not_found
def list_documents(connection: sqlite3.Connection, case_number: str) -> dict[str, Any]:
    """Índice dos documentos (id, tipo, autor, data, páginas) sem o texto, com os advogados e o lado de cada um."""
    rows = connection.execute(LIST_DOCUMENTS_QUERY, (_resolve_case_id(connection, case_number),)).fetchall()
    own_case_number = extract_case_number(case_number)
    sides = _lawyer_sides(rows)
    lawyers = _lawyers(rows, sides)
    return {
        "found": True,
        "case_number": own_case_number,
        "documents": [_document_metadata(row, sides) for row in rows],
        "lawyers": lawyers,
        "warnings": _signature_warnings(rows) + [
            f"Documento {row['id']}: {warning[0].lower()}{warning[1:]}"
            for row in rows
            for warning in _cited_case_number_warnings(row["texto"], own_case_number)
        ] + [
            f"{lawyer['name']} ({lawyer['oab']}) assina peças dos dois lados (autor e réu) neste processo; merece conferência."
            for lawyer in lawyers
            if lawyer["side"] == "ambos os lados"
        ],
    }


@_reports_not_found
def read_document(connection: sqlite3.Connection, document_id: int) -> dict[str, Any]:
    """Texto completo de um documento, com processo, tipo, autor e data para citar a fonte. Único que devolve texto."""
    row = connection.execute(READ_DOCUMENT_QUERY, (document_id,)).fetchone()
    if row is None:
        raise DocumentNotFoundError(f"Documento {document_id} não encontrado no banco.")
    return {
        "found": True,
        "id": row["id"],
        "case_number": row["numero"],
        "type": row["tipo"],
        "author": row["autor"],
        "date": brazilian_date(row["dt_juntada"]),
        "pages": row["num_paginas"],
        "text": row["texto"],
        "warnings": _cited_case_number_warnings(row["texto"], row["numero"]),
        "source": document_source(row["id"], row["tipo"], row["dt_juntada"]),
    }


@_reports_not_found
def check_draft_basis(connection: sqlite3.Connection, case_number: str) -> dict[str, Any]:
    """Diz se o processo tem as peças que uma minuta de sentença exige (petição inicial e contestação) e quais faltam."""
    case_id = _resolve_case_id(connection, case_number)
    present = {row["tipo"] for row in connection.execute(DRAFT_BASIS_QUERY, (case_id, *DRAFT_REQUIRED_DOCUMENT_TYPES))}
    missing = [document_type for document_type in DRAFT_REQUIRED_DOCUMENT_TYPES if document_type not in present]
    return {"found": True, "case_number": extract_case_number(case_number), "ready": not missing, "missing": missing}


def _cited_case_number_warnings(text: str, own_case_number: str) -> list[str]:
    """Números de processo citados no texto ("Autos n.", "Processo n.") que não são o do processo dono do documento."""
    return [
        f"O texto cita o processo {number}, mas o documento pertence ao processo {own_case_number}. "
        "Merece conferência: pode ser documento juntado no processo errado."
        for number in extract_case_numbers(text)
        if number != own_case_number
    ]


@_reports_not_found
def search_text(
    connection: sqlite3.Connection,
    term: str,
    case_number: str | None = None,
    document_type: str | None = None,
    limit: int = SEARCH_DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Documentos que mencionam um termo, com um trecho em volta; filtros opcionais por processo e tipo de documento."""
    words = WORD_PATTERN.findall(term)
    if not words:
        return {"found": False, "message": f"O termo '{term}' não tem palavras para buscar."}
    ensure_search_index(connection)
    canonical_type = _canonical_document_type(connection, document_type) if document_type else None
    if document_type and canonical_type is None:
        valid_types = [row["tipo"] for row in connection.execute("SELECT DISTINCT tipo FROM documento ORDER BY tipo")]
        return {"found": False, "message": f"Tipo de documento '{document_type}' não existe. Tipos: {', '.join(valid_types)}."}
    filters = {
        "case_id": _resolve_case_id(connection, case_number) if case_number else None,
        "document_type": canonical_type,
        "limit": max(1, min(limit, SEARCH_MAX_LIMIT)),
    }
    for match_mode, query in _search_queries(words):
        total = connection.execute(SEARCH_TEXT_COUNT_QUERY, {**filters, "query": query}).fetchone()["total"]
        if total:
            rows = connection.execute(SEARCH_TEXT_QUERY, {**filters, "query": query}).fetchall()
            return {
                "found": True,
                "term": term,
                "match": match_mode,
                "total": total,
                "results": [
                    {"document_id": row["id"], "case_number": row["numero"], "type": row["tipo"],
                     "date": brazilian_date(row["dt_juntada"]), "snippet": row["trecho"],
                     "source": document_source(row["id"], row["tipo"], row["dt_juntada"])}
                    for row in rows
                ],
            }
    return {"found": False, "message": f"Nenhum documento menciona '{term}'."}


def search_parties(connection: sqlite3.Connection, name: str) -> dict[str, Any]:
    """Pessoas cujo nome contém as palavras buscadas, separadas por CPF/CNPJ, com os processos e o polo de cada uma."""
    words = WORD_PATTERN.findall(name)
    if not words:
        return {"found": False, "message": f"O nome '{name}' não tem palavras para buscar."}
    ensure_search_index(connection)
    query = " ".join(f'"{word}"' for word in words)
    documents = [row["documento"] for row in connection.execute(MATCHING_PARTY_DOCUMENTS_QUERY, (query,))]
    if not documents:
        return {"found": False, "message": f"Nenhuma parte com o nome '{name}'."}

    people = _people_by_document(connection, documents)
    shown = people[:SEARCH_PARTIES_MAX_PEOPLE]
    result: dict[str, Any] = {
        "found": True,
        "query": name,
        "total_people": len(people),
        "people": [
            {**person, "cases": person["cases"][:SEARCH_PARTIES_MAX_CASES]} for person in shown
        ],
        "warnings": [
            f"O documento {person['document']} aparece no cadastro com nomes diferentes: {', '.join(person['names'])}."
            for person in shown
            if len(person["names"]) > 1
        ],
    }
    if len(people) > 1:
        result["homonym_notice"] = (
            f"Encontrei {len(people)} pessoas diferentes com esse nome (CPF/CNPJ distintos). De qual delas se trata?"
        )
    return result


def search_cases(
    connection: sqlite3.Connection,
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
    limit: int = SEARCH_CASES_DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Processos por atributo: assunto, classe, comarca, vara, magistrado, situação, período e valor — total e lista.

    Filtros de texto são "contém", sem diferença de acento e de maiúsculas. Datas no formato AAAA-MM-DD.
    Ordenação: "filing_date" (autuação), "sentence_date" ou "claim_value", sempre do maior para o menor.
    """
    dates = [filing_date_from, filing_date_to, sentence_date_from, sentence_date_to]
    if any(date is not None and not ISO_DATE_PATTERN.fullmatch(date) for date in dates):
        return {"found": False, "message": "Use datas no formato AAAA-MM-DD (ex.: 2024-01-31)."}
    if order_by not in SEARCH_CASES_ORDER_COLUMNS:
        return {"found": False, "message": f"Ordenação '{order_by}' inválida. Use: {', '.join(SEARCH_CASES_ORDER_COLUMNS)}."}

    # (nome do filtro para o usuário, condição SQL, valor como veio, valor normalizado para comparar)
    value_filters = [
        (label, condition, value, normalize(value))
        for label, condition, value, normalize in [
            ("assunto", "comparable_text(p.assunto) LIKE ?", subject, _contains),
            ("classe", "comparable_text(p.classe) LIKE ?", case_class, _contains),
            ("comarca", "comparable_district(p.comarca) LIKE ?", district, _contains_district),
            ("vara", "comparable_text(u.vara) LIKE ?", court_unit, _contains),
            ("magistrado", "comparable_text(m.nome) LIKE ?", judge, _contains),
            ("situação", "LOWER(TRIM(p.situacao)) = ?", status, comparable_text),
        ]
        if value
    ]
    conditions = [condition for _, condition, _, _ in value_filters]
    parameters: list[Any] = [normalized for _, _, _, normalized in value_filters]
    range_filters = [
        ("p.dt_aut >=", filing_date_from), ("p.dt_aut <=", filing_date_to),
        ("p.data_sentenca >=", sentence_date_from), ("p.data_sentenca <=", sentence_date_to),
        ("p.valor_causa >=", claim_value_min), ("p.valor_causa <=", claim_value_max),
    ]
    conditions += [f"{expression} ?" for expression, value in range_filters if value is not None]
    parameters += [value for _, value in range_filters if value is not None]
    if not conditions:
        return {"found": False, "message": "Informe ao menos um filtro (assunto, classe, comarca, vara, magistrado, situação, datas ou valor)."}

    where = " WHERE " + " AND ".join(conditions)
    total = connection.execute(f"SELECT COUNT(*) AS total {SEARCH_CASES_FROM}{where}", parameters).fetchone()["total"]
    if not total:
        return {"found": False, "message": _no_case_found_message(connection, value_filters)}
    order_column = SEARCH_CASES_ORDER_COLUMNS[order_by]
    rows = connection.execute(
        f"SELECT p.numero, p.classe, p.assunto, p.comarca, LOWER(TRIM(p.situacao)) AS situacao, p.dt_aut, p.valor_causa"
        f" {SEARCH_CASES_FROM}{where} ORDER BY {order_column} IS NULL, {order_column} DESC, p.numero LIMIT ?",
        [*parameters, max(1, min(limit, SEARCH_CASES_MAX_LIMIT))],
    ).fetchall()
    return {
        "found": True,
        "total": total,
        "cases": [
            {"case_number": row["numero"], "case_class": row["classe"], "subject": row["assunto"],
             "district": row["comarca"], "status": row["situacao"], "filing_date": brazilian_date(row["dt_aut"]),
             "claim_value": row["valor_causa"]}
            for row in rows
        ],
    }


def _contains(value: str) -> str:
    return f"%{comparable_text(value)}%"


def _contains_district(value: str) -> str:
    return f"%{comparable_district(value)}%"


def _no_case_found_message(connection: sqlite3.Connection, value_filters: list[tuple[str, str, str, str]]) -> str:
    """Diz qual filtro não corresponde a nada no banco; se todos existem, o vazio vem da combinação."""
    for label, condition, value, normalized in value_filters:
        alone = connection.execute(f"SELECT 1 {SEARCH_CASES_FROM} WHERE {condition} LIMIT 1", (normalized,)).fetchone()
        if alone is None:
            return _unknown_filter_value_message(connection, label, value)
    if len(value_filters) > 1:
        return "Nenhum processo atende a todos os filtros juntos; cada um, sozinho, encontra processos."
    return "Nenhum processo atende aos filtros."


def _unknown_filter_value_message(connection: sqlite3.Connection, label: str, value: str) -> str:
    message = f"Não há {label} com '{value}' no banco."
    values_query = SEARCH_CASES_FILTER_VALUES_QUERIES[label]
    if values_query is None:
        return message
    plural_label, query = values_query
    values = [row[0] for row in connection.execute(query)]
    return f"{message} {plural_label} que existem: {', '.join(values)}."


def _people_by_document(connection: sqlite3.Connection, documents: list[str]) -> list[dict[str, Any]]:
    query = PARTY_CASES_QUERY.format(placeholders=", ".join("?" * len(documents)))
    people: dict[str, dict[str, Any]] = {}
    for row in connection.execute(query, documents):
        person = people.setdefault(
            row["documento"],
            {"document": row["documento"], "person_type": _person_type(row["documento"]), "names": [], "cases": []},
        )
        if row["nome"] not in person["names"]:
            person["names"].append(row["nome"])
        case = {"case_number": row["numero"], "role": ROLE_BY_POLE[row["polo"]]}
        if case not in person["cases"]:
            person["cases"].append(case)
    for person in people.values():
        person["names"].sort()
        person["case_count"] = len({case["case_number"] for case in person["cases"]})
    return sorted(people.values(), key=lambda person: (-person["case_count"], person["document"]))


def _search_queries(words: list[str]) -> list[tuple[str, str]]:
    """Primeiro a frase exata; se houver mais de uma palavra, depois todas elas em qualquer ordem.

    Cada palavra vai entre aspas: o termo do usuário nunca é interpretado como sintaxe do FTS5.
    """
    queries = [("frase exata", '"' + " ".join(words) + '"')]
    if len(words) > 1:
        queries.append(("todas as palavras", " ".join(f'"{word}"' for word in words)))
    return queries


def _canonical_document_type(connection: sqlite3.Connection, document_type: str) -> str | None:
    wanted = comparable_text(document_type)
    for row in connection.execute("SELECT DISTINCT tipo FROM documento"):
        if comparable_text(row["tipo"]) == wanted:
            return row["tipo"]
    return None


def _oab(text: str) -> str | None:
    match = OAB_PATTERN.search(text)
    return f"OAB/{match.group(1)} {match.group(2)}" if match else None


def _signed_oabs(text: str) -> list[str]:
    """Todas as OABs do texto: a petição de acordo, por exemplo, é assinada pelos advogados dos dois lados."""
    return list(dict.fromkeys(f"OAB/{state} {number}" for state, number in OAB_PATTERN.findall(text)))


def _lawyer_sides(rows: list[sqlite3.Row]) -> dict[str, str]:
    sides_by_oab: dict[str, set[str]] = {}
    for row in rows:
        oab, anchor_side = _oab(row["autor"]), SIDE_BY_ANCHOR_DOCUMENT_TYPE.get(row["tipo"])
        if oab is not None:
            sides_by_oab.setdefault(oab, set())
            if anchor_side is not None:
                sides_by_oab[oab].add(anchor_side)
    return {oab: _side_label(sides) for oab, sides in sides_by_oab.items()}


def _side_label(sides: set[str]) -> str:
    if len(sides) > 1:
        return "ambos os lados"
    return next(iter(sides), "não identificado")


def _document_metadata(row: sqlite3.Row, sides: dict[str, str]) -> dict[str, Any]:
    oab = _oab(row["autor"])
    return {
        "id": row["id"],
        "type": row["tipo"],
        "author": row["autor"],
        "date": brazilian_date(row["dt_juntada"]),
        "pages": row["num_paginas"],
        "lawyer_side": sides[oab] if oab else None,
        "source": document_source(row["id"], row["tipo"], row["dt_juntada"]),
    }


def _lawyers(rows: list[sqlite3.Row], sides: dict[str, str]) -> list[dict[str, Any]]:
    lawyers: dict[str, dict[str, Any]] = {}
    for row in rows:
        oab = _oab(row["autor"])
        if oab is None:
            continue
        lawyer = lawyers.setdefault(
            oab, {"name": row["autor"].split(" — ")[0], "oab": oab, "side": sides[oab], "document_ids": []}
        )
        lawyer["document_ids"].append(row["id"])
    return list(lawyers.values())


def _signature_warnings(rows: list[sqlite3.Row]) -> list[str]:
    warnings = []
    for row in rows:
        registered, signed = _oab(row["autor"]), _signed_oabs(row["texto"])
        if registered is not None and signed and registered not in signed:
            warnings.append(
                f"Documento {row['id']}: o autor cadastrado ({row['autor']}) "
                f"difere da assinatura no texto ({', '.join(signed)})."
            )
    return warnings


def _party_card(row: sqlite3.Row) -> dict[str, str]:
    return {"name": row["nome"], "person_type": _person_type(row["documento"]), "document": row["documento"]}


def _person_type(document: str | None) -> str:
    """Pelo formato do documento; o campo parte.tipo não serve: é do cadastro da pessoa, não do processo."""
    if document is not None and len(document) == CPF_LENGTH:
        return "pessoa física"
    if document is not None and len(document) == CNPJ_LENGTH:
        return "pessoa jurídica"
    return "não identificado"
