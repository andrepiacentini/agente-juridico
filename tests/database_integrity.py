"""Impressão digital (SHA-256) do banco original, usada para provar que nenhum teste o altera (D27, D31)."""

import hashlib
from pathlib import Path

REFERENCE_DATABASE_SHA256 = "8a90b47cdc3b07bcb395ffe0e81c3d56dd33946fa047dec7dc86499767690c43"


def sha256_of(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()
