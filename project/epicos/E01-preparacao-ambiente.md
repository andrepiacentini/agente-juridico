# E01 — Preparação do ambiente

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** qualquer pessoa clona o repositório, roda `uv sync` e tem o projeto pronto, com o modelo local respondendo.
**Por que vem primeiro:** tudo o mais depende de um ambiente que se reproduz igual em qualquer máquina.

---

### T1.1 — Instalar o gerenciador de projeto `uv` `[x]`
- **Objetivo:** ter o `uv` disponível no terminal.
- **Passos:** `brew install uv`; conferir com `uv --version`.
- **Pronto quando:** o comando mostra a versão instalada.
- **Depende de:** nada.

### T1.2 — Baixar e testar o modelo local `[x]`
- **Objetivo:** confirmar que o modelo local roda no MacBook. Resultado: `qwen3:4b-instruct-2507-q4_K_M` (D25).
- **Passos:** `ollama pull qwen3:4b-instruct-2507-q4_K_M`; `ollama run qwen3:4b-instruct-2507-q4_K_M "Responda em português: o que é uma petição inicial?"`.
- **Pronto quando:** o modelo responde em português sem travar a máquina.
- **Depende de:** nada.

### T1.3 — Iniciar o repositório Git `[x]`
- **Objetivo:** ter o projeto versionado desde o início.
- **Passos:** `git init` (se ainda não feito); criar `.gitignore` com `.venv/`, `.env`, `__pycache__/`, `.chainlit/`.
- **Pronto quando:** `git status` não lista arquivos de ambiente nem segredos.
- **Depende de:** nada.

### T1.4 — Decidir se o banco `desafio.sqlite` entra no repositório `[x]`
- **Objetivo:** tomar e registrar uma decisão sobre versionar ou não o arquivo do banco.
- **Passos:** ver o tamanho do arquivo; avaliar se a banca já tem o arquivo; decidir entre commitar ou instruir o download no README; registrar no `DECISOES.md`.
- **Pronto quando:** a decisão está no `DECISOES.md` e o `.gitignore` reflete a escolha.
- **Depende de:** T1.3.

### T1.5 — Criar o `pyproject.toml` `[x]`
- **Objetivo:** declarar o projeto, a versão do Python (3.12) e as bibliotecas.
- **Passos:** `uv init --package --name case-assistant --python 3.12`; `uv add "pydantic-ai-slim[openai,anthropic]" chainlit python-dotenv` (D29); `uv add --dev pytest`; declarar o comando `case-assistant` apontando para `case_assistant.cli:main`.
- **Pronto quando:** `uv sync` termina sem erro e `uv run python --version` mostra 3.12.
- **Depende de:** T1.1.

### T1.6 — Criar o esqueleto de pastas `[x]`
- **Objetivo:** ter a estrutura de arquivos prevista no `plan.md` §6, ainda vazia.
- **Passos:** criar `src/case_assistant/` com `__init__.py`, `db.py`, `tools.py`, `prompts.py`, `agent.py`, `cli.py`; criar `tests/` e `app.py`.
- **Pronto quando:** `uv run python -c "import case_assistant"` funciona.
- **Depende de:** T1.5.

### T1.7 — Criar o `.env.example` `[x]`
- **Objetivo:** documentar como escolher o modelo sem mexer no código.
- **Passos:** criar `.env.example` com `LLM_MODEL=ollama:qwen3:4b-instruct-2507-q4_K_M` e a alternativa comentada `# LLM_MODEL=anthropic:claude-sonnet-5`, mais `OLLAMA_BASE_URL=http://localhost:11434/v1` (exigido pelo Pydantic AI para o prefixo `ollama:`) e `ANTHROPIC_API_KEY=`; procurar chaves no histórico inteiro do Git (o passo original "primeiro commit" deixou de fazer sentido: o repositório já tinha histórico).
- **Pronto quando:** o `.env.example` carrega e resolve o modelo local, e nem o repositório nem o histórico contêm chave real ou arquivo `.env`.
- **Depende de:** T1.3 a T1.6.

### T1.8 — Baixar e testar o modelo reserva `[x]`
- **Objetivo:** ter o `qwen3:1.7b` pronto como plano B e saber quanto ele ganha em velocidade e memória.
- **Passos:** verificar com `ollama show` se a etiqueta aponta para uma versão só-raciocínio (D25); `ollama pull qwen3:1.7b`; rodar a mesma pergunta da T1.2 três vezes com `think=false`; anotar velocidade, tempo, memória e qualidade no comparativo do `plan.md` §5.
- **Pronto quando:** o comparativo tem a coluna do 1.7b preenchida.
- **Depende de:** T1.2.

### T1.9 — Testar o modelo em nuvem (Gemini) `[x]`
- **Objetivo:** completar o comparativo com um modelo em nuvem e confirmar que a alternativa em nuvem funciona, sem custo (D30).
- **Passos:** instalar o conector do Google (`pydantic-ai-slim[...,google]`); criar uma chave gratuita em aistudio.google.com e colocá-la no `.env` como `GOOGLE_API_KEY` (nunca no código nem no Git); rodar a mesma pergunta da T1.2 três vezes com o `gemini-3.8-flash`; anotar velocidade, tempo e qualidade na coluna "Gemini (nuvem)" do comparativo do `plan.md` §5.
- **Pronto quando:** o comparativo tem as colunas dos dois modelos locais e do Gemini preenchidas.
- **Depende de:** T1.7.

### T1.10 — Testar o Claude em nuvem (opcional) `[ ]`
- **Opcional (D30):** depende de haver crédito na conta da Anthropic; a API recusa chamadas sem saldo.
- **Objetivo:** acrescentar o Claude ao comparativo e mostrar o mesmo agente com três fornecedores (local, Google, Anthropic).
- **Passos:** colocar crédito na conta Anthropic; preencher `ANTHROPIC_API_KEY` no `.env`; rodar a mesma pergunta da T1.2 três vezes com o `claude-sonnet-5`; preencher a coluna "Claude (nuvem)" do comparativo.
- **Pronto quando:** a coluna do Claude está preenchida, ou a tarefa é cancelada no fim do projeto por falta de crédito.
- **Depende de:** T1.7.

### T1.11 — Rodar os testes na CI a cada pull request `[x]`
- **Objetivo:** os testes viram uma etapa de todo PR no GitHub, sem depender de rodá-los na máquina de quem desenvolve (D33).
- **Passos:** criar `.github/workflows/tests.yml` com GitHub Actions: em todo pull request e em push na `main`, instalar com `uv sync --locked` e rodar `uv run pytest`; sem chaves de API (os testes não usam IA); acrescentar a regra "merge só com o check `tests` verde" ao fluxo de branches do `AGENTS.md` e o selo de status ao README.
- **Pronto quando:** o PR desta tarefa mostra o check `tests` verde no GitHub.
- **Depende de:** T1.5, T1.6.
