"""Número do processo no padrão CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO): a chave de todas as consultas."""

import re

# Os separadores são opcionais para aceitar tanto o número formatado quanto os 20 dígitos corridos;
# os limites (?<!\d) e (?!\d) impedem que um trecho de um número maior seja confundido com um processo.
CASE_NUMBER_PATTERN = re.compile(r"(?<!\d)(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})(?!\d)")


def extract_case_number(text: str) -> str | None:
    """Devolve o primeiro número de processo do texto, já formatado, ou `None` se não houver."""
    match = CASE_NUMBER_PATTERN.search(text)
    if match is None:
        return None
    sequence, check_digits, year, justice, court, origin = match.groups()
    return f"{sequence}-{check_digits}.{year}.{justice}.{court}.{origin}"
