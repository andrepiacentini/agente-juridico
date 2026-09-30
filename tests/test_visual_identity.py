"""Identidade visual do chat (T14.1): imagem do TJSC, subtítulo e crédito do autor. Sem IA e sem navegador.

O Chainlit serve `public/logo_light.*`, `public/logo_dark.*` e `public/favicon.*` sozinho; o subtítulo e o crédito não
têm lugar nativo na tela inicial e entram por um script e uma folha de estilo que a configuração injeta.
"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent
PUBLIC = ROOT / "public"
CONFIG = tomllib.loads((ROOT / ".chainlit" / "config.toml").read_text(encoding="utf-8"))["UI"]
SUBTITLE = "Desafio técnico: Agente de IA para análise de processos"
# Na tela: "Desenvolvido por André Piacentini (site · LinkedIn) em setembro de 2026", com os dois links.
CREDIT_PARTS = ("Desenvolvido por André Piacentini (", ") em setembro de 2026")
SITE_URL = "https://andrepiacentini.com.br"
LINKEDIN_URL = "https://www.linkedin.com/in/andrepiacentini/"


def public_file(url: str) -> Path:
    assert url.startswith("/public/"), url
    return PUBLIC / url.removeprefix("/public/")


def test_logo_for_each_theme_and_favicon_are_in_public() -> None:
    for name in ("logo_light.png", "logo_dark.png", "favicon.png"):
        assert (PUBLIC / name).is_file(), name


def test_config_injects_the_identity_script_and_stylesheet_that_exist() -> None:
    assert public_file(CONFIG["custom_js"]).is_file()
    assert public_file(CONFIG["custom_css"]).is_file()


def test_script_has_the_subtitle_and_the_credit_with_both_links() -> None:
    script = public_file(CONFIG["custom_js"]).read_text(encoding="utf-8")

    for text in (SUBTITLE, *CREDIT_PARTS, SITE_URL, LINKEDIN_URL):
        assert text in script, text


def test_script_builds_the_page_without_injecting_html() -> None:
    # Montar os elementos com textContent, e não com innerHTML, evita que texto vire marcação.
    script = public_file(CONFIG["custom_js"]).read_text(encoding="utf-8")

    assert "innerHTML" not in script
    assert 'rel = "noopener noreferrer"' in script
