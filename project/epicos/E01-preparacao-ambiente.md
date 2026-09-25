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
- **Para explicar à banca:** "O `uv` garante que o projeto rode com a mesma versão de Python e das bibliotecas em qualquer máquina."

### T1.2 — Baixar e testar o modelo local `[x]`
- **Objetivo:** confirmar que o modelo local roda no MacBook. Resultado: `qwen3:4b-instruct-2507-q4_K_M` (D25).
- **Passos:** `ollama pull qwen3:4b-instruct-2507-q4_K_M`; `ollama run qwen3:4b-instruct-2507-q4_K_M "Responda em português: o que é uma petição inicial?"`.
- **Pronto quando:** o modelo responde em português sem travar a máquina.
- **Depende de:** nada.
- **Para explicar à banca:** "Escolhi um modelo de 4 bilhões de parâmetros porque é o maior que cabe com folga em 8 GB e ainda sabe usar ferramentas."

### T1.3 — Iniciar o repositório Git `[x]`
- **Objetivo:** ter o projeto versionado desde o início.
- **Passos:** `git init` (se ainda não feito); criar `.gitignore` com `.venv/`, `.env`, `__pycache__/`, `.chainlit/`.
- **Pronto quando:** `git status` não lista arquivos de ambiente nem segredos.
- **Depende de:** nada.
- **Para explicar à banca:** "O histórico de commits mostra a evolução do projeto e complementa o `DECISOES.md`."

### T1.4 — Decidir se o banco `desafio.sqlite` entra no repositório `[x]`
- **Objetivo:** tomar e registrar uma decisão sobre versionar ou não o arquivo do banco.
- **Passos:** ver o tamanho do arquivo; avaliar se a banca já tem o arquivo; decidir entre commitar ou instruir o download no README; registrar no `DECISOES.md`.
- **Pronto quando:** a decisão está no `DECISOES.md` e o `.gitignore` reflete a escolha.
- **Depende de:** T1.3.
- **Para explicar à banca:** "Decidi [commitar / não commitar] o banco porque [motivo] — e em nenhum caso o arquivo é alterado pelo projeto."

### T1.5 — Criar o `pyproject.toml` `[x]`
- **Objetivo:** declarar o projeto, a versão do Python (3.12) e as bibliotecas.
- **Passos:** `uv init --package --name case-assistant --python 3.12`; `uv add "pydantic-ai-slim[openai,anthropic]" chainlit python-dotenv` (D29); `uv add --dev pytest`; declarar o comando `case-assistant` apontando para `case_assistant.cli:main`.
- **Pronto quando:** `uv sync` termina sem erro e `uv run python --version` mostra 3.12.
- **Depende de:** T1.1.
- **Para explicar à banca:** "Fixei o Python 3.12 porque o do sistema é 3.14 e algumas bibliotecas ainda não têm versão pronta para ele."

### T1.6 — Criar o esqueleto de pastas `[x]`
- **Objetivo:** ter a estrutura de arquivos prevista no `plan.md` §6, ainda vazia.
- **Passos:** criar `src/case_assistant/` com `__init__.py`, `db.py`, `tools.py`, `prompts.py`, `agent.py`, `cli.py`; criar `tests/` e `app.py`.
- **Pronto quando:** `uv run python -c "import case_assistant"` funciona.
- **Depende de:** T1.5.
- **Para explicar à banca:** "Separei banco, ferramentas, instruções do agente e interface em arquivos diferentes — cada um se explica sozinho."

### T1.7 — Criar o `.env.example` e fazer o primeiro commit `[ ]`
- **Objetivo:** documentar como escolher o modelo sem mexer no código.
- **Passos:** criar `.env.example` com `LLM_MODEL=ollama:qwen3:4b-instruct-2507-q4_K_M` e a alternativa comentada `# LLM_MODEL=anthropic:claude-sonnet-5`, mais `OLLAMA_BASE_URL=http://localhost:11434/v1` (exigido pelo Pydantic AI para o prefixo `ollama:`) e `ANTHROPIC_API_KEY=`; primeiro commit.
- **Pronto quando:** o commit existe e não contém nenhuma chave real.
- **Depende de:** T1.3 a T1.6.
- **Para explicar à banca:** "Trocar de modelo é mudar uma linha de configuração; o código é o mesmo."

### T1.8 — Baixar e testar o modelo reserva `[x]`
- **Objetivo:** ter o `qwen3:1.7b` pronto como plano B e saber quanto ele ganha em velocidade e memória.
- **Passos:** verificar com `ollama show` se a etiqueta aponta para uma versão só-raciocínio (D25); `ollama pull qwen3:1.7b`; rodar a mesma pergunta da T1.2 três vezes com `think=false`; anotar velocidade, tempo, memória e qualidade no comparativo do `plan.md` §5.
- **Pronto quando:** o comparativo tem a coluna do 1.7b preenchida.
- **Depende de:** T1.2.
- **Para explicar à banca:** "O modelo reserva é duas vezes mais rápido e ocupa metade da memória, mas escreve pior — por isso é reserva, e não o padrão."

### T1.9 — Testar o modelo em nuvem `[ ]`
- **Objetivo:** completar o comparativo com o Claude e confirmar que a alternativa em nuvem funciona.
- **Passos:** obter uma `ANTHROPIC_API_KEY` e colocá-la no `.env` (nunca no código nem no Git); rodar a mesma pergunta da T1.2 três vezes com o Claude Sonnet 5 (o modelo do `.env.example`); anotar velocidade, tempo e qualidade na coluna "Claude (nuvem)" do comparativo do `plan.md` §5.
- **Pronto quando:** o comparativo tem as três colunas preenchidas.
- **Depende de:** T1.7.
- **Para explicar à banca:** "Comparei os três modelos com a mesma pergunta: o local protege dados sigilosos, o de nuvem é o mais capaz, e trocar entre eles é uma linha de configuração."
