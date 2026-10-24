# Assistente de IA para consulta de processos judiciais — Teste Técnico TJSC

[![tests](https://github.com/andrepiacentini/desafio-tjsc/actions/workflows/tests.yml/badge.svg)](https://github.com/andrepiacentini/desafio-tjsc/actions/workflows/tests.yml)

Chat de IA que responde, em português, perguntas sobre uma base de processos judiciais sintéticos (`desafio.sqlite`). O agente decide sozinho o que consultar no banco, cita os documentos e movimentações em que baseou cada resposta e declara quando a informação não existe na base. Também resume processos e gera propostas de minuta de sentença, sempre identificadas como texto não proferido.

## O que ele faz

- **Resume** um processo pelo número (ex.: `0000007-79.2023.8.99.9014`): fatos, pedidos, defesa, andamento e resultado.
- **Mostra** partes, magistrado e advogados, e aponta inconsistências do cadastro (juiz aposentado, comarca grafada de outro jeito, nomes repetidos com CPF diferente).
- **Responde** se o processo foi julgado, com a decisão e os fundamentos quando o texto da sentença está no banco.
- **Propõe** uma minuta de sentença, sempre aberta com **PROPOSTA DE MINUTA — texto não proferido**, e recusa quando faltam a petição inicial e a contestação.
- **Diz "não consta"** quando o dado não existe — o banco foi construído com armadilhas para testar isso, e cada uma tem um teste.
- **Conversa:** depois da primeira pergunta sobre um processo, as seguintes podem omitir o número ("e quem é o juiz?").

Toda resposta cita a fonte no formato `[doc 7878 — Sentença, 18/02/2026]`, `[mov. 9219 — …]` ou `[cadastro do processo]`, e a interface web mostra cada consulta ao banco como um passo abaixo da resposta.

## Como rodar

### Pré-requisitos

- **8 GB de RAM** ou mais. O projeto foi desenvolvido e medido num MacBook M1 de 8 GB; o modelo local sozinho ocupa cerca de 3,9 GB.
- **Git**, **[uv](https://docs.astral.sh/uv/)** (instala o Python 3.12 e as dependências; o Python do sistema não é usado) e, para o modelo local, o **[Ollama](https://ollama.com/download)** aberto. Com o Gemini ou o Claude na nuvem, basta a chave de API (ver [Trocar de modelo](#trocar-de-modelo)).

Os comandos de instalação de cada sistema estão abaixo; depois deles, os passos são os mesmos.

| Sistema | Situação |
|---|---|
| macOS (Apple Silicon) | é onde o projeto foi desenvolvido e medido |
| Linux: Ubuntu 24.04, Debian 12, Fedora 42 | seguido do zero em contêineres limpos em 30/09/2026 (D86): instalação, 406 testes, chat web e Ollama com as duas variáveis |
| Windows 10 e 11 | comandos das fontes oficiais do uv e do Ollama; **não testado** numa máquina Windows |

#### macOS

```bash
brew install git uv                           # ou: curl -LsSf https://astral.sh/uv/install.sh | sh
```

O Ollama vem do instalador em <https://ollama.com/download>; depois de instalado, fica aberto na barra de menus.

#### Linux (Ubuntu, Debian, Fedora)

```bash
sudo apt install git curl zstd                # Ubuntu e Debian
sudo dnf install git curl zstd                # Fedora
curl -LsSf https://astral.sh/uv/install.sh | sh     # uv; abra um terminal novo depois
curl -fsSL https://ollama.com/install.sh | sh       # Ollama; já sobe como serviço do systemd
```

O `zstd` é exigido pelo instalador do Ollama, que falha sem ele. Sem placa de vídeo NVIDIA ou AMD, o Ollama roda o modelo no processador, bem mais devagar que num Mac com Apple Silicon; para esse caso, o Gemini na nuvem é o caminho.

#### Windows

No PowerShell:

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e           # ou: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
winget install --id Ollama.Ollama -e          # ou o instalador em https://ollama.com/download/windows
```

Feche e abra o PowerShell depois, para ele encontrar os comandos novos. Alternativa: o [WSL 2](https://learn.microsoft.com/windows/wsl/install) com Ubuntu, seguindo os passos do Linux dentro dele.

### Instalação

Em qualquer sistema (no Windows, no PowerShell):

```bash
git clone https://github.com/andrepiacentini/desafio-tjsc.git
cd desafio-tjsc
uv sync                                       # cria o .venv com o Python 3.12 e tudo que está no uv.lock (alguns minutos na primeira vez)
ollama pull qwen3:4b-instruct-2507-q4_K_M     # modelo local (~2,5 GB); pule se for usar só a nuvem
cp .env.example .env                          # no PowerShell: Copy-Item .env.example .env
```

O `.env.example` já vem com o modelo local como padrão. Com o modelo local, ajuste o Ollama uma vez — janela de contexto de 16 mil tokens e cache comprimido — conforme [Modelo local (Ollama)](#modelo-local-ollama-janela-de-contexto-e-cache), para o seu sistema. Sem isso, o resumo de um processo com peças lidas passa da janela padrão e o Ollama recusa o pedido.

O banco `desafio.sqlite` já está no repositório e é aberto **somente para leitura**; o projeto nunca o altera.

### Chat no navegador

```bash
uv run chainlit run app.py -w
```

O navegador abre sozinho em <http://localhost:8000>. A tela inicial oferece as quatro perguntas do edital como atalhos. Cada resposta traz, abaixo, "Consultou o banco de dados" com os passos do agente (o que ele pediu e o que o banco devolveu), o consumo de tokens e o custo. A engrenagem ao lado do campo de mensagem troca o modelo sem perder a conversa; o botão "Ver consumo" abre o painel de uso e a projeção de custo mensal.

### Chat no terminal

```bash
uv run case-assistant
```

Mesmo agente, sem interface gráfica: é o plano B da demonstração. Cada ferramenta chamada aparece como `→ find_case(...)` antes da resposta. `sair` encerra.

### Perguntas para começar

As quatro perguntas do edital, sobre o processo de referência (19 documentos, sentença parcialmente procedente, juiz aposentado):

1. `Resuma o processo 0000007-79.2023.8.99.9014, destacando os principais fatos e o andamento processual.`
2. `Quem são as partes, o magistrado e os advogados do processo 0000007-79.2023.8.99.9014? Quais são os pedidos apresentados?`
3. `O processo 0000007-79.2023.8.99.9014 já foi julgado? Se sim, qual foi a decisão e quais foram seus fundamentos?`
4. `Elabore uma minuta de sentença para o processo 0000007-79.2023.8.99.9014, com base nos fatos e documentos disponíveis.`

Para ver o agente reconhecer limites, repita as mesmas perguntas com o processo `0000001-43.2021.8.99.9014`, que não tem nenhum documento: o resumo sai só pelo andamento e a minuta é recusada.

### Trocar de modelo

O código não tem caminho especial por fornecedor: a troca é só no `.env`, na variável `LLM_MODEL`.

| Modelo | `.env` | Observações |
|---|---|---|
| **Local (padrão):** Qwen3 4B no Ollama | `LLM_MODEL=ollama:qwen3:4b-instruct-2507-q4_K_M` | nada sai da máquina; 45 s a 3,5 min por resposta ([D78](DECISOES.md)) |
| **Nuvem, gratuito:** Gemini 3.8 Flash | `LLM_MODEL=google:gemini-3.8-flash`<br>`LLM_THINKING=low`<br>`GOOGLE_API_KEY=...` | chave em [Google AI Studio](https://aistudio.google.com/apikey); ~5 s por resposta; é o modelo da demonstração |
| **Nuvem, opcional:** Claude Sonnet 5.5 | `LLM_MODEL=anthropic:claude-sonnet-5-5`<br>`LLM_THINKING=low`<br>`ANTHROPIC_API_KEY=...` | exige crédito na conta Anthropic; 3 a 15 s por resposta; com o cache do prompt, as 4 perguntas do edital numa conversa custaram R$ 0,62, contra R$ 0,84 no Gemini ([D84 e D87](DECISOES.md)) |

Para oferecer mais de um modelo no seletor da interface web, liste-os em `LLM_MODEL_OPTIONS` (o raciocínio de cada um vai depois de `@`):

```bash
LLM_MODEL_OPTIONS=ollama:qwen3:4b-instruct-2507-q4_K_M,google:gemini-3.8-flash@low,anthropic:claude-sonnet-5-5@low
```

Todas as variáveis estão comentadas em [`.env.example`](.env.example).

### Testes e bateria de avaliação

```bash
uv run pytest                                   # ~400 testes; não usam IA e rodam na CI em todo PR
uv run pytest tests/test_tools.py -k "without_documents"   # um teste
uv run case-assistant-eval                      # bateria de 20 conversas (tests/golden.yaml) com o modelo do .env
uv run case-assistant-eval --model google:gemini-3.8-flash --case edital-1-resumo-3161 --output respostas.json
```

Os testes cobrem as armadilhas do banco (processos sem documento, situação com caixa mista, juiz ausente, homônimos, movimentações órfãs, SQL que tenta escrever) sem chamar nenhum modelo. A bateria roda o agente de verdade e confere critérios por resposta (ferramenta chamada, trechos obrigatórios e proibidos); os placares ficam em [`docs/avaliacao/`](docs/avaliacao/README.md).

## Definições tomadas

| Item | Escolha |
|---|---|
| **Linguagem** | Python 3.12, gerenciado pelo [uv](https://docs.astral.sh/uv/) |
| **Frameworks** | [Pydantic AI](https://ai.pydantic.dev/) (laço do agente e ferramentas; pacote enxuto com os provedores Ollama, Google e Anthropic) · [Chainlit](https://chainlit.io/) (interface web de chat) |
| **Bibliotecas** | `sqlite3` da biblioteca padrão, com [FTS5](https://www.sqlite.org/fts5.html) para busca textual · `python-dotenv` para ler o `.env` · `pytest` para os testes · `plotly` para os gráficos do painel de consumo |
| **Provedor de modelo** | [Ollama](https://ollama.com/) com `qwen3:4b-instruct-2507-q4_K_M` (Qwen3 4B sem modo raciocínio), rodando localmente (padrão) · Google Gemini 3.8 Flash na nuvem, pelo plano gratuito (alternativa) · Anthropic Claude Sonnet 5.5 na nuvem (opcional, com crédito). A troca é feita pela variável de ambiente `LLM_MODEL`, sem alterar o código |
| **Arquitetura** | Agente com ferramentas tipadas sobre SQL, **sem RAG vetorial**. As ferramentas devolvem primeiro os metadados (ids, tipos, datas) e o texto de um documento só quando ele é pedido. Uma ferramenta de SQL livre, restrita a consultas de leitura, cobre perguntas imprevistas. O banco é aberto somente para leitura |

As justificativas de cada escolha e as alternativas descartadas estão em [`DECISOES.md`](DECISOES.md); a análise do edital e do banco, em [`docs/plan.md`](docs/plan.md).

## Como funciona

O modelo recebe as instruções, a pergunta e dez ferramentas, e decide sozinho quais chamar e em que ordem. Cada chamada é uma função Python que consulta o SQLite e devolve um resultado compacto:

| Ferramenta | O que devolve |
|---|---|
| `find_case` | cadastro do processo: classe, assunto, situação, magistrado, unidade, valor, sinais de julgamento e avisos do cadastro |
| `list_parties` | partes nos polos ativo e passivo, com documento, e os advogados extraídos das peças |
| `list_movements` | andamento (código, descrição, data), com avisos de ordem estranha |
| `list_documents` | id, tipo, data e autor de cada peça — **nunca o texto** |
| `read_document` | o texto de uma peça, pelo id |
| `search_text`, `search_parties`, `search_cases` | busca por palavras nas peças, por nome de parte e por filtros do cadastro |
| `prepare_draft` | confere se há petição inicial e contestação e reúne o material da minuta |
| `run_sql` | consulta livre, só `SELECT`, com limite de linhas e de tentativas — a válvula de escape |

Regras que atravessam o código: o banco abre com `mode=ro` e os índices de busca ficam em tabelas temporárias, nunca no arquivo; a situação de julgamento cruza três sinais (data da sentença, movimentação de julgamento e documento de sentença) e reporta quando eles não batem; o papel de uma parte é sempre o polo do processo, não o tipo do cadastro; toda resposta cita a fonte, e um validador devolve ao modelo a resposta que afirma algo sobre um processo que ele não consultou.

Camadas, de baixo para cima: `db.py` (acesso) → `tools.py` (domínio) → `agent.py` (agente, com `prompts.py` e `session.py`) → `cli.py` e `app.py` (apresentação). A apresentação nunca faz SQL; o acesso a dados nunca conhece o agente.

## Modelo local (Ollama): janela de contexto e cache

O agente fala com o Ollama pelo endpoint compatível com OpenAI, que ignora o tamanho de contexto pedido a cada chamada; por isso a janela e a compressão do cache são configuradas **no servidor, uma vez** ([D77](DECISOES.md)). Sem isso, um resumo com peças lidas passa de 8 mil tokens e o Ollama recusa o pedido. São dois ajustes: **janela de 16 mil tokens** e **cache comprimido (`q8_0`)**, que corta pela metade a memória da janela (1,2 GB em vez de 2,4 GB nos 16k).

### macOS

1. **Janela:** no app do Ollama, abra *Settings* e ponha *Context length* em **16k**. É essa preferência que vale — ela sobrepõe a variável `OLLAMA_CONTEXT_LENGTH`.
2. **Cache:**

   ```bash
   launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0      # vale até reiniciar o Mac
   # para valer a cada login:
   cp docs/ollama/local.ollama-kv-cache.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/local.ollama-kv-cache.plist
   ```

   Depois, feche e abra o app do Ollama.

### Linux

O Ollama roda como serviço do `systemd`, e as duas variáveis vão nele:

```bash
sudo systemctl edit ollama.service
```

No editor que abrir, acrescente e salve:

```ini
[Service]
Environment="OLLAMA_CONTEXT_LENGTH=16384"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Sem `systemd` (contêiner, WSL sem `systemd`): `OLLAMA_CONTEXT_LENGTH=16384 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve`. Foi assim que as duas variáveis foram conferidas nos testes em contêiner.

### Windows

1. **Janela:** no app do Ollama, abra *Settings* e ponha *Context length* em **16k**, como no Mac.
2. **Cache:** no PowerShell, grave a variável na sua conta e reinicie o Ollama (clique no ícone dele ao lado do relógio, *Quit Ollama*, e abra de novo pelo menu Iniciar):

   ```powershell
   [Environment]::SetEnvironmentVariable("OLLAMA_KV_CACHE_TYPE", "q8_0", "User")
   ```

### Para conferir

Depois de uma pergunta, `ollama ps` mostra `CONTEXT` em `16384` e o modelo em cerca de 3,9 GB. Com isso o modelo, a janela e o sistema cabem em cerca de 7 dos 8 GB; feche os demais programas.

## Mapa das pastas

```
desafio-tjsc/
├── README.md                 este arquivo
├── DECISOES.md               registro de decisões, por dia, em linguagem simples
├── AGENTS.md                 instruções para assistentes de IA (o CLAUDE.md só o importa)
├── desafio.sqlite            banco do edital, somente leitura, versionado de propósito
├── desafio_tecnico_detalhes.pdf   edital
├── app.py                    interface web (Chainlit)
├── chainlit.md               tela de boas-vindas do chat
├── public/                   imagem do TJSC (temas claro e escuro), favicon e o subtítulo e o crédito da tela inicial
├── prices.toml               preços dos modelos e cenários da projeção de custo
├── .env.example              todas as variáveis de ambiente, comentadas
├── usage.sqlite              registro de consumo, criado na primeira resposta; fora do Git
├── src/case_assistant/       o pacote: db, tools, agent, prompts, session, cli, avaliação, uso e custo
├── tests/                    testes sem IA (pytest) e a bateria de avaliação (golden.yaml)
├── docs/
│   ├── plan.md               análise do edital e do banco, arquitetura decidida
│   ├── glossario.md          termos técnicos em linguagem simples, citados pelo DECISOES.md
│   ├── avaliacao/            placares da bateria por modelo e data
│   ├── roteiros/             cenários testados à mão, com as saídas dos modelos
│   ├── ai_use/               como a IA foi usada no desenvolvimento e onde atrapalhou
│   └── ollama/               LaunchAgent do cache do Ollama
├── project/                  ROADMAP.md e um arquivo por épico, com as tarefas
└── .github/workflows/        CI: pytest em todo PR e push na main
```
