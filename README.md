# Assistente de IA para consulta de processos judiciais — Desafio TJSC

[![tests](https://github.com/andrepiacentini/desafio-tjsc/actions/workflows/tests.yml/badge.svg)](https://github.com/andrepiacentini/desafio-tjsc/actions/workflows/tests.yml)

Chat de IA que responde, em português, perguntas sobre uma base de processos judiciais sintéticos (`desafio.sqlite`). O agente decide sozinho o que consultar no banco, cita os documentos e movimentações em que baseou cada resposta e declara quando a informação não existe na base. Também resume processos e gera propostas de minuta de sentença, sempre identificadas como texto não proferido.

## Definições tomadas

| Item | Escolha |
|---|---|
| **Linguagem** | Python 3.12, gerenciado pelo [uv](https://docs.astral.sh/uv/) |
| **Frameworks** | [Pydantic AI](https://ai.pydantic.dev/) (laço do agente e ferramentas; pacote enxuto com os provedores Ollama, Google e Anthropic) · [Chainlit](https://chainlit.io/) (interface web de chat) |
| **Bibliotecas** | `sqlite3` da biblioteca padrão, com [FTS5](https://www.sqlite.org/fts5.html) para busca textual · `python-dotenv` para ler o `.env` · `pytest` para os testes |
| **Provedor de modelo** | [Ollama](https://ollama.com/) com `qwen3:4b-instruct-2507-q4_K_M` (Qwen3 4B sem modo raciocínio), rodando localmente (padrão) · Google Gemini 3.8 Flash na nuvem, pelo plano gratuito (alternativa) · Anthropic Claude na nuvem (opcional, com crédito). A troca é feita pela variável de ambiente `LLM_MODEL`, sem alterar o código |
| **Arquitetura** | Agente com ferramentas tipadas sobre SQL, **sem RAG vetorial**. As ferramentas devolvem primeiro os metadados (ids, tipos, datas) e o texto de um documento só quando ele é pedido. Uma ferramenta de SQL livre, restrita a consultas de leitura, cobre perguntas imprevistas. O banco é aberto somente para leitura |

As justificativas de cada escolha e as alternativas descartadas estão em [`DECISOES.md`](DECISOES.md).

## Modelo local (Ollama): janela de contexto e cache

O agente fala com o Ollama pelo endpoint compatível com OpenAI, que ignora o tamanho de contexto pedido a cada chamada; por isso a janela e a compressão do cache são configuradas **no servidor, uma vez** ([D77](DECISOES.md)). Sem isso, um resumo com peças lidas passa de 8 mil tokens e o Ollama recusa o pedido.

1. **Janela de 16 mil tokens:** no app do Ollama, abra *Settings* e ponha *Context length* em **16k**. É essa preferência que vale — ela sobrepõe a variável `OLLAMA_CONTEXT_LENGTH`.
2. **Cache comprimido (`q8_0`)**, que corta pela metade a memória da janela (1,2 GB em vez de 2,4 GB nos 16k):

   ```bash
   launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0      # vale até reiniciar o Mac
   # para valer a cada login:
   cp docs/ollama/local.ollama-kv-cache.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/local.ollama-kv-cache.plist
   ```

   Depois, feche e abra o app do Ollama.

Para conferir: depois de uma pergunta, `ollama ps` mostra `CONTEXT` em `16384` e o modelo em cerca de 3,9 GB.
