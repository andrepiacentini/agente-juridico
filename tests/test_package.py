"""Garante que o pacote instala e expõe os módulos do esqueleto."""

import importlib

import pytest

SKELETON_MODULES = ("db", "tools", "prompts", "agent", "cli")


@pytest.mark.parametrize("module_name", SKELETON_MODULES)
def test_skeleton_module_imports(module_name: str) -> None:
    importlib.import_module(f"case_assistant.{module_name}")
