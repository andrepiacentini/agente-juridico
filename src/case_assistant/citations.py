"""Data e fonte já no formato da resposta, num lugar só (T7.7, D53).

O modelo local erra ao converter datas (deu 09/11/2025 no lugar de 2025-11-17) e copia o que a ferramenta devolve.
Por isso as ferramentas entregam a data e a citação prontas, e o modelo só copia.
"""

REGISTRY_SOURCE = "[cadastro do processo]"


def brazilian_date(iso_date: str | None) -> str | None:
    """AAAA-MM-DD do banco para DD/MM/AAAA; sem data, continua sem data."""
    if iso_date is None:
        return None
    year, month, day = iso_date.split("-")
    return f"{day}/{month}/{year}"


def movement_source(code: int, description: str, iso_date: str) -> str:
    return f"[mov. {code} — {description}, {brazilian_date(iso_date)}]"


def document_source(document_id: int, document_type: str, iso_date: str) -> str:
    return f"[doc {document_id} — {document_type}, {brazilian_date(iso_date)}]"
