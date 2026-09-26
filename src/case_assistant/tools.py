"""Ferramentas que o agente chama para consultar o banco; devolvem metadados e só leem texto sob demanda (E03, E04)."""

import sqlite3
from typing import Any

from case_assistant.case_number import extract_case_number

# LEFT JOIN: 1.044 processos não têm magistrado e não podem sumir da consulta.
# LOWER(TRIM()): a situação vem como "Julgado", "JULGADO" ou "julgado" e é devolvida sempre em minúsculas.
FIND_CASE_QUERY = """
    SELECT p.id, p.numero, p.classe, p.assunto, p.comarca, p.dt_aut, p.data_sentenca, p.valor_causa,
           LOWER(TRIM(p.situacao)) AS situacao,
           u.vara, u.comarca AS unidade_comarca,
           m.nome AS magistrado_nome, m.situacao AS magistrado_situacao,
           (SELECT COUNT(*) FROM documento WHERE processo_id = p.id) AS total_documentos,
           (SELECT COUNT(*) FROM movimentacao WHERE processo_id = p.id) AS total_movimentacoes
    FROM processo p
    LEFT JOIN unidade u ON u.id = p.unidade_id
    LEFT JOIN magistrado m ON m.id = p.magistrado_id
    WHERE p.numero = ?
"""


def find_case(connection: sqlite3.Connection, case_number: str) -> dict[str, Any]:
    """Cartão de identificação do processo: classe, assunto, vara, magistrado, datas, valor e totais."""
    normalized_number = extract_case_number(case_number)
    if normalized_number is None:
        return _not_found(f"Não reconheci um número de processo no padrão CNJ em '{case_number}'.")

    row = connection.execute(FIND_CASE_QUERY, (normalized_number,)).fetchone()
    if row is None:
        return _not_found(f"Processo {normalized_number} não encontrado no banco.")

    return {
        "found": True,
        "case_number": row["numero"],
        "case_class": row["classe"],
        "subject": row["assunto"],
        "district": row["comarca"],
        "court_unit": row["vara"],
        "court_unit_district": row["unidade_comarca"],
        "judge": _judge(row),
        "filing_date": row["dt_aut"],
        "sentence_date": row["data_sentenca"],
        "claim_value": row["valor_causa"],
        "status": row["situacao"],
        "document_count": row["total_documentos"],
        "movement_count": row["total_movimentacoes"],
    }


def _judge(row: sqlite3.Row) -> dict[str, str] | None:
    if row["magistrado_nome"] is None:
        return None
    return {"name": row["magistrado_nome"], "status": row["magistrado_situacao"]}


def _not_found(message: str) -> dict[str, Any]:
    return {"found": False, "message": message}
