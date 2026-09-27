"""Comparação de textos do banco sem acento, sem diferença de caixa e de espaços — nunca para exibir, só para comparar."""

import unicodedata

# Abreviações de comarca encontradas no banco ("S. José", "Bal. Camboriú", "Sto. Amaro da Imperatriz").
DISTRICT_ABBREVIATIONS = {"s.": "sao", "sto.": "santo", "bal.": "balneario"}


def comparable_text(text: str | None) -> str | None:
    if text is None:
        return None
    without_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(without_accents.lower().split())


def comparable_district(district: str | None) -> str | None:
    """Como `comparable_text`, com as abreviações de comarca do banco por extenso (D34)."""
    if district is None:
        return None
    return " ".join(DISTRICT_ABBREVIATIONS.get(word, word) for word in comparable_text(district).split())
