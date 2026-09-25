# Assistente de IA para consulta de processos judiciais — Desafio TJSC

Chat de IA que responde, em português, perguntas sobre uma base de processos judiciais sintéticos (`desafio.sqlite`). O agente decide sozinho o que consultar no banco, cita os documentos e movimentações em que baseou cada resposta e declara quando a informação não existe na base. Também resume processos e gera propostas de minuta de sentença, sempre identificadas como texto não proferido.

## Definições tomadas

| Item | Escolha |
|---|---|
| **Linguagem** | Python 3.12, gerenciado pelo [uv](https://docs.astral.sh/uv/) |
| **Frameworks** | [Pydantic AI](https://ai.pydantic.dev/) (laço do agente e ferramentas; pacote enxuto com os provedores Ollama e Anthropic) · [Chainlit](https://chainlit.io/) (interface web de chat) |
| **Bibliotecas** | `sqlite3` da biblioteca padrão, com [FTS5](https://www.sqlite.org/fts5.html) para busca textual · `python-dotenv` para ler o `.env` · `pytest` para os testes |
| **Provedor de modelo** | [Ollama](https://ollama.com/) com `qwen3:4b-instruct-2507-q4_K_M` (Qwen3 4B sem modo raciocínio), rodando localmente (padrão) · Anthropic Claude na nuvem (alternativa). A troca é feita pela variável de ambiente `LLM_MODEL`, sem alterar o código |
| **Arquitetura** | Agente com ferramentas tipadas sobre SQL, **sem RAG vetorial**. As ferramentas devolvem primeiro os metadados (ids, tipos, datas) e o texto de um documento só quando ele é pedido. Uma ferramenta de SQL livre, restrita a consultas de leitura, cobre perguntas imprevistas. O banco é aberto somente para leitura |

As justificativas de cada escolha e as alternativas descartadas estão em [`DECISOES.md`](DECISOES.md).
