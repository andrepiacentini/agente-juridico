"""Guarda de toda rodada de testes: o `desafio.sqlite` original tem que terminar idêntico ao recebido (T2.3)."""

import pytest
from database_integrity import REFERENCE_DATABASE_SHA256, sha256_of

from case_assistant.db import DEFAULT_DATABASE_PATH


@pytest.fixture(scope="session", autouse=True)
def original_database_is_never_modified():
    assert sha256_of(DEFAULT_DATABASE_PATH) == REFERENCE_DATABASE_SHA256, (
        "O desafio.sqlite já estava diferente do recebido antes dos testes; restaure com `git checkout -- desafio.sqlite`."
    )
    yield
    assert sha256_of(DEFAULT_DATABASE_PATH) == REFERENCE_DATABASE_SHA256, (
        "Algum teste alterou o desafio.sqlite original; restaure com `git checkout -- desafio.sqlite`."
    )
