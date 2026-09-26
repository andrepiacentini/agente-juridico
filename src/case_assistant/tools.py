"""Ferramentas que o agente chama para consultar o banco; devolvem metadados e só leem texto sob demanda (E03, E04)."""

import functools
import sqlite3
import unicodedata
from collections.abc import Callable
from typing import Any

from case_assistant.case_number import extract_case_number

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
CPF_LENGTH, CNPJ_LENGTH = 14, 18  # "999.539.988-87" e "99.193.997/0001-35"
INACTIVE_JUDGE_STATUSES = ("aposentado", "removido")
ACTIVE_UNIT_STATUS = "ativa"
# Acima disso só existe um valor no banco: 9.999.999.999, com cara de preenchimento; o seguinte é 1,27 milhão.
IMPLAUSIBLE_CLAIM_VALUE = 100_000_000
STATUSES_WITHOUT_SENTENCE = ("em andamento", "suspenso")
# Abreviações de comarca encontradas no banco ("S. José", "Bal. Camboriú", "Sto. Amaro da Imperatriz").
DISTRICT_ABBREVIATIONS = {"s.": "sao", "sto.": "santo", "bal.": "balneario"}


class CaseNotFoundError(Exception):
    """O texto não traz um número de processo no padrão CNJ, ou o processo não está no banco."""


def _reports_missing_case(tool: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    """Fronteira da ferramenta: "processo não encontrado" vira resposta para o agente, não erro."""

    @functools.wraps(tool)
    def tool_with_missing_case_answer(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return tool(*args, **kwargs)
        except CaseNotFoundError as error:
            return {"found": False, "message": str(error)}

    return tool_with_missing_case_answer


def _resolve_case_id(connection: sqlite3.Connection, case_number: str) -> int:
    normalized_number = extract_case_number(case_number)
    if normalized_number is None:
        raise CaseNotFoundError(f"Não reconheci um número de processo no padrão CNJ em '{case_number}'.")
    row = connection.execute("SELECT id FROM processo WHERE numero = ?", (normalized_number,)).fetchone()
    if row is None:
        raise CaseNotFoundError(f"Processo {normalized_number} não encontrado no banco.")
    return row["id"]


@_reports_missing_case
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
        "filing_date": row["dt_aut"],
        "sentence_date": row["data_sentenca"],
        "claim_value": row["valor_causa"],
        "status": row["situacao"],
        "document_count": row["total_documentos"],
        "movement_count": row["total_movimentacoes"],
        "judgment": _judgment(connection, row["id"], row["data_sentenca"]),
    }
    case["warnings"] = _registry_warnings(case)
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
        if _comparable_district(district) == _comparable_district(unit_district):
            warnings.append(
                f"A comarca está grafada de forma diferente no processo ('{district}') e na vara ('{unit_district}')."
            )
        else:
            warnings.append(f"Comarca do processo ('{district}') difere da comarca da vara ('{unit_district}').")

    claim_value = case["claim_value"]
    if claim_value is None:
        warnings.append("Valor da causa não informado.")
    elif claim_value <= 0:
        warnings.append(f"Valor da causa inválido ({claim_value}).")
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


def _comparable_district(district: str) -> str:
    """Só para comparar: sem acento, sem diferença de caixa e de espaços, com as abreviações do banco por extenso."""
    without_accents = unicodedata.normalize("NFKD", district).encode("ascii", "ignore").decode()
    words = without_accents.lower().split()
    return " ".join(DISTRICT_ABBREVIATIONS.get(word, word) for word in words)


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
    return {"code": movement["codigo"], "description": movement["descricao"], "date": movement["data_mov"]}


def _document_card(document: sqlite3.Row | None) -> dict[str, Any] | None:
    if document is None:
        return None
    return {"id": document["id"], "type": document["tipo"], "date": document["dt_juntada"]}


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


@_reports_missing_case
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
    }


@_reports_missing_case
def list_movements(connection: sqlite3.Connection, case_number: str) -> dict[str, Any]:
    """Andamento do processo em ordem de data: só data, código e descrição de cada movimentação."""
    rows = connection.execute(LIST_MOVEMENTS_QUERY, (_resolve_case_id(connection, case_number),)).fetchall()
    return {
        "found": True,
        "case_number": extract_case_number(case_number),
        "movements": [{"date": row["data_mov"], "code": row["codigo"], "description": row["descricao"]} for row in rows],
        "warnings": _timeline_warnings(rows),
    }


def _timeline_warnings(rows: list[sqlite3.Row]) -> list[str]:
    """Sequências incomuns no andamento, reportadas para conferência humana — podem ser exceções legítimas."""
    final_judgment_dates = [row["data_mov"] for row in rows if row["codigo"] == FINAL_JUDGMENT_CODE]
    if not final_judgment_dates:
        return []
    final_judgment_date = min(final_judgment_dates)
    warnings = [
        f"Recurso de apelação registrado em {row['data_mov']}, depois do trânsito em julgado ({final_judgment_date}). "
        "Sequência incomum, que merece conferência: pode ser recurso interposto fora do prazo ou erro de cadastro."
        for row in rows
        if row["codigo"] == APPEAL_CODE and row["data_mov"] > final_judgment_date
    ]
    if not any(row["codigo"] in SENTENCE_MOVEMENT_CODES for row in rows):
        warnings.append(
            f"Trânsito em julgado ({final_judgment_date}) sem movimentação de sentença no andamento. "
            "Merece conferência: a sentença pode não ter sido registrada."
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
