"""Reconhecimento do número do processo no padrão CNJ dentro de um texto livre."""

from contextlib import closing

import pytest

from case_assistant.db import connect
from case_assistant.case_number import extract_case_number, extract_case_numbers, has_valid_check_digits

REFERENCE_CASE_NUMBER = "0000007-79.2023.8.99.9014"


@pytest.mark.parametrize(
    "text",
    [
        "resuma o 0000007-79.2023.8.99.9014",
        "Quem é o juiz do processo 0000007-79.2023.8.99.9014?",
        "processo 00000077920238999014, por favor",
        "0000007-79.2023.8.99.9014",
    ],
    ids=["formatted", "question", "digits_only", "number_alone"],
)
def test_extracts_and_formats_case_number(text: str) -> None:
    assert extract_case_number(text) == REFERENCE_CASE_NUMBER


@pytest.mark.parametrize(
    "text",
    ["resuma o processo", "", "valor da causa 1234567", "000000779202389990141"],
    ids=["no_number", "empty", "short_number", "twenty_one_digits"],
)
def test_returns_none_without_case_number(text: str) -> None:
    assert extract_case_number(text) is None


def test_extracts_well_formed_number_even_if_it_is_not_in_the_database() -> None:
    assert extract_case_number("e o 9999999-99.2099.8.99.9999?") == "9999999-99.2099.8.99.9999"


def test_returns_first_number_when_text_has_several() -> None:
    text = "compare 0000007-79.2023.8.99.9014 com 0000001-43.2021.8.99.9014"

    assert extract_case_number(text) == REFERENCE_CASE_NUMBER


def test_extracts_every_case_number_of_the_text_in_order() -> None:
    text = "compare o 0000007-79.2023.8.99.9014 com o 00000014320218999014 e de novo o 0000007-79.2023.8.99.9014"

    assert extract_case_numbers(text) == [REFERENCE_CASE_NUMBER, "0000001-43.2021.8.99.9014"]


def test_extracts_no_case_number_from_text_without_one() -> None:
    assert extract_case_numbers("resuma o processo") == []


def test_reference_case_number_has_valid_check_digits() -> None:
    assert has_valid_check_digits(REFERENCE_CASE_NUMBER) is True


@pytest.mark.parametrize(
    "number",
    ["0000007-78.2023.8.99.9014", "0000007-79.2024.8.99.9014", "0000008-79.2023.8.99.9014"],
    ids=["check_digit_typo", "year_typo", "sequence_typo"],
)
def test_a_typo_breaks_the_check_digits(number: str) -> None:
    assert has_valid_check_digits(number) is False


def test_every_case_number_in_the_database_has_valid_check_digits() -> None:
    with closing(connect()) as connection:
        numbers = [row["numero"] for row in connection.execute("SELECT numero FROM processo")]

    assert len(numbers) == 10_000
    assert all(has_valid_check_digits(number) for number in numbers)
