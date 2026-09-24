# AGENTS.md

This file provides guidance to AI coding agents (Codex, Cursor, Copilot, Gemini CLI, Claude Code) when working with code in this repository.

## O projeto

Desafio técnico do TJSC (processo seletivo): um chat de IA em português que responde perguntas sobre `desafio.sqlite` (processos judiciais sintéticos), consultando o banco de forma autônoma, citando os dados usados e declarando quando não há dado. O edital está em `desafio_tecnico_detalhes.pdf`; a análise completa e a arquitetura decidida estão em **`docs/plan.md` — leia-o antes de qualquer trabalho de implementação**. `DECISOES.md` (a criar) é entregável obrigatório: registre lá cada decisão relevante e cada erro do assistente de IA no momento em que acontecer, não no fim.

Idioma: **identificadores do código em inglês** (ver [Padrão de codificação](#padrão-de-codificação)); comentários, docstrings, prompts, docs, mensagens e respostas do agente em **português**.

Este é o arquivo único de instruções para assistentes de IA. O `CLAUDE.md` só importa este arquivo (`@AGENTS.md`) para o Claude Code: **edite sempre aqui**, nunca o `CLAUDE.md`.

## Estado atual

Repositório recém-iniciado, sem commits e sem código. Existem o PDF, o banco, `DECISOES.md`, `docs/plan.md`, `docs/glossario.md` e o planejamento em `project/` (`ROADMAP.md` + um arquivo por épico em `project/epicos/`, tarefas `T<épico>.<n>`). Ao concluir uma tarefa, marque `[x]` no épico e atualize a situação no `ROADMAP.md`. A estrutura-alvo do código (`src/case_assistant/`, `tests/`, `app.py`) está em `plan.md` §6.

`DECISOES.md` é organizado por dia (`## DD/MM/AAAA`), entradas `Dnn` com **Decisão / Por quê / Descartado**, em linguagem simples; todo termo técnico leva link para uma âncora de `docs/glossario.md` (criar a âncora se não existir).

## Comandos (planejados — válidos após a Fase 0 criar o `pyproject.toml`)

```bash
brew install uv                    # uv não está instalado nesta máquina
uv sync                            # Python 3.12 pinado; o Python do sistema é 3.14
ollama pull qwen3:4b               # modelo local padrão
uv run case-assistant              # chat no terminal (cli.py) — plano B da demo
uv run chainlit run app.py -w      # UI web
uv run pytest                      # testes das ferramentas (não precisam de LLM)
uv run pytest tests/test_tools.py -k "sem_documentos"   # um teste
```

Troca de LLM só por variável de ambiente (`LLM_MODEL` em `.env`): `ollama:qwen3:4b` local ou `anthropic:...` na nuvem. O código não pode ter branch por provedor.

## Arquitetura — decisões fechadas

**Agente com ferramentas tipadas sobre SQL (Pydantic AI). Não é RAG vetorial.** As perguntas do edital são ancoradas em número de processo (chave exata) e um processo inteiro cabe no contexto de um modelo de 4B; embeddings/Qdrant foram avaliados e descartados (`plan.md` §3). Não reintroduza chunking, banco vetorial ou LlamaIndex/LangChain.

Regras que atravessam todo o código:

- **Banco é somente leitura.** Abrir sempre com `file:desafio.sqlite?mode=ro`. Índices FTS5 e views auxiliares vão em `TEMP`, nunca no arquivo. O arquivo `desafio.sqlite` não é modificado nem commitado com alterações.
- **Metadados primeiro, texto sob demanda.** Ferramentas de listagem devolvem ids/tipos/datas, nunca `documento.texto`; só `ler_documento(id)` devolve texto. É o que faz o agente caber em 8 GB de RAM com `qwen3:4b`.
- **`consultar_sql` é válvula de escape, não caminho principal.** Só `SELECT`/`WITH`, sem `;`, `PRAGMA`, `ATTACH`; `LIMIT` forçado; timeout. Erros do SQLite voltam ao modelo como observação, com teto de tentativas.
- **Toda resposta cita a fonte** (`documento.id` + tipo + data, ou a movimentação). A UI (Chainlit) exibe cada tool call como passo — a fundamentação tem que ser visível.
- **`processo_em_foco`** é estado explícito da sessão, injetado no system prompt a cada turno; ferramentas o usam quando a pergunta não traz número.
- **Minuta de sentença** sempre abre com "PROPOSTA DE MINUTA — texto não proferido" e é recusada se não houver petição inicial e contestação.

## Padrão de codificação

### Regra 1 — Identificadores em inglês

Todo elemento estrutural do código é nomeado em inglês: pacotes, módulos, classes, métodos, funções, variáveis, constantes, parâmetros, modelos Pydantic e seus campos, nomes das ferramentas do agente, funções de teste, e todo objeto de banco que o projeto criar (tabelas e views em `TEMP`, índices FTS5, aliases de coluna).

- Continuam em português: comentários, docstrings, textos de prompt, mensagens ao usuário, logs legíveis e documentação.
- **Exceção:** o schema do `desafio.sqlite` é dado externo e somente leitura. Tabelas e colunas (`processo`, `data_sentenca`, …) mantêm o nome original dentro do SQL; a tradução acontece na fronteira, com alias (`SELECT data_sentenca AS sentence_date`) ou no mapeamento para o modelo (`Case.sentence_date`).
- Um termo do domínio tem **uma única tradução** em todo o código (processo → `case`, movimentação → `movement`, parte → `party`, magistrado → `judge`, unidade → `court_unit`, sentença → `sentence`, minuta → `draft`). Termo novo: escolha a tradução uma vez e reutilize.
- Nomes em português citados neste arquivo, no `plan.md` e nos épicos (`ler_documento`, `consultar_sql`, `processo_em_foco`) são conceituais; na implementação recebem o equivalente em inglês.

### Regra 2 — Clean Code (Robert C. Martin, "Uncle Bob")

- **Nomes revelam intenção.** Sem abreviações, prefixos de tipo ou números mágicos; constantes nomeadas (`JUDGMENT_MOVEMENT_CODES = (9219, 9220, 9221)`).
- **Funções pequenas, fazem uma coisa**, num único nível de abstração, com poucos parâmetros e sem efeito colateral escondido. Função que consulta não altera estado.
- **Comentário explica o porquê**, nunca o quê. Código comentado é apagado.
- **Erros com exceções específicas**, nunca engolidas nem trocadas por `None` silencioso. A conversão de erro em observação para o modelo acontece em um só lugar, na fronteira da ferramenta.
- **Regra do escoteiro:** deixe o trecho que você tocou mais limpo do que encontrou — sem refatorar o que não foi tocado.

### Boas práticas de arquitetura

Aplicadas na proporção do projeto: é um desafio técnico com prazo, rodando num notebook de 8 GB. Em conflito entre princípios, **KISS e YAGNI desempatam**.

- **SOLID.** Uma responsabilidade por classe/módulo; dependa de abstrações nas fronteiras (o agente não conhece o provedor de LLM — ver "Troca de LLM" acima; as ferramentas recebem a conexão, não a abrem).
- **KISS e YAGNI.** Nenhuma abstração, camada, configuração ou recurso antes de uma necessidade concreta. Uma interface com uma implementação só é suspeita.
- **DRY.** Cada regra de negócio mora num único lugar — ex.: normalização de `situacao`, cruzamento dos três sinais de julgamento, formatação da citação de fonte.
- **Camadas.** Acesso a dados (SQLite) → domínio/ferramentas → agente → apresentação (CLI e Chainlit). A dependência só aponta para baixo; a apresentação nunca faz SQL e o acesso a dados nunca conhece o agente.
- **Monólito modular.** Um único pacote Python com módulos coesos; sem serviços separados, filas ou APIs internas.
- **DDD leve.** A estrutura e os nomes do código seguem o domínio jurídico (linguagem ubíqua, com a tradução fixa da Regra 1); regras do domínio ficam no domínio, não na UI nem no prompt.
- **Testes automatizados com TDD** nas ferramentas e regras de domínio: cada armadilha do banco (seção abaixo) ganha um teste antes do código que a trata. Percentual de cobertura não é meta (`DECISOES.md` D15).
- **Observabilidade.** `logging` com campos estruturados — nunca `print` — em cada chamada de ferramenta: nome, argumentos, duração e número de linhas devolvidas.
- **12 fatores.** Configuração só por variável de ambiente (`.env`, com `.env.example` versionado); nenhum caminho, modelo ou chave fixo no código; dependências declaradas no `pyproject.toml`/`uv.lock`.

## O banco é adversarial por design

Os números abaixo custaram uma sessão de profiling; não os re-derive, use-os para escrever tools e testes. Detalhes em `plan.md` §2.

- 7 tabelas: `processo` (10.000) no centro; `documento` (25.582, texto íntegro ~21 MB), `movimentacao` (134.046), `processo_parte`/`parte`, `magistrado`, `unidade`. Datas são texto ISO `YYYY-MM-DD`.
- **63% dos processos (6.309) não têm documento nenhum.** Resumo só por movimentações; minuta impossível.
- `situacao` tem casing misto (`Julgado`/`JULGADO`/`julgado`) — sempre `LOWER()`.
- Situação de julgamento nunca vem de um sinal só: cruzar `data_sentenca`, movimentação `9219/9220/9221` e documento tipo `Sentença`. Há 4.426 processos com `data_sentenca` sem documento de sentença e 37 no sentido inverso.
- `magistrado_id` NULL em 1.044 processos; 2.022 processos têm juiz `aposentado`/`removido`; 1.024 têm `processo.comarca ≠ unidade.comarca`. Reportar, nunca inferir ou "corrigir".
- 402 movimentações órfãs (processo inexistente) — só aparecem sem JOIN.
- 643 nomes de parte homônimos com CPF diferente — pedir desambiguação.
- **Advogados não têm tabela.** Estão em `documento.autor` ("Dr. X — OAB/SC 99.170") e no texto; o metadado `autor` às vezes diverge da assinatura no texto.
- Casos de referência: **3161** (`0000007-79.2023.8.99.9014`, 19 docs, sentença parcialmente procedente, juiz aposentado) e **1** (`0000001-43.2021.8.99.9014`, zero docs, `julgado` minúsculo).

## Ambiente do autor

MacBook M1 com 8 GB — orçamento de memória em `plan.md` §5. Ollama já instalado. Priorize latência e respostas compactas das ferramentas sobre elegância.
