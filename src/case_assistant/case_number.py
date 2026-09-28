"""Número do processo no padrão CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO): a chave de todas as consultas."""

import re

# Os separadores são opcionais para aceitar tanto o número formatado quanto os 20 dígitos corridos;
# os limites (?<!\d) e (?!\d) impedem que um trecho de um número maior seja confundido com um processo.
CASE_NUMBER_PATTERN = re.compile(r"(?<!\d)(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})(?!\d)")
# Resolução CNJ 65/2008: com os dígitos verificadores movidos para o fim, o número inteiro deixa resto 1 na divisão por 97.
CHECK_DIGITS_MODULUS = 97
VALID_CHECK_REMAINDER = 1


def extract_case_number(text: str) -> str | None:
    """Devolve o primeiro número de processo do texto, já formatado, ou `None` se não houver."""
    match = CASE_NUMBER_PATTERN.search(text)
    if match is None:
        return None
    return _formatted(match)


def extract_case_numbers(text: str) -> list[str]:
    """Todos os números de processo do texto, formatados, sem repetição e na ordem em que aparecem."""
    return list(dict.fromkeys(_formatted(match) for match in CASE_NUMBER_PATTERN.finditer(text)))


def has_valid_check_digits(case_number: str) -> bool:
    """Confere os dígitos verificadores (módulo 97): um dígito digitado errado quase sempre quebra a conta."""
    match = CASE_NUMBER_PATTERN.search(case_number)
    if match is None:
        return False
    sequence, check_digits, year, justice, court, origin = match.groups()
    return int(f"{sequence}{year}{justice}{court}{origin}{check_digits}") % CHECK_DIGITS_MODULUS == VALID_CHECK_REMAINDER


def check_digits(case_number: str) -> str:
    """Os dois dígitos verificadores do número (o "DD" de NNNNNNN-DD.AAAA.J.TR.OOOO)."""
    return CASE_NUMBER_PATTERN.search(case_number).group(2)


def _formatted(match: re.Match[str]) -> str:
    sequence, check_digits, year, justice, court, origin = match.groups()
    return f"{sequence}-{check_digits}.{year}.{justice}.{court}.{origin}"
