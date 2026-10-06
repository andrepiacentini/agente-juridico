# Placares da bateria de avaliação

Cada arquivo `placar-<modelo>-<data>.json` é a saída de `uv run case-assistant-eval --output …` (T9.4): para cada caso de [`tests/golden.yaml`](../../tests/golden.yaml), as perguntas, as respostas, as ferramentas chamadas, as falhas e o tempo. Análise e decisão: [`DECISOES.md`](../../DECISOES.md) D65.

## 28/09/2026 — 19 casos

| Modelo | Placar | Tempo total | Arquivo |
|---|---|---|---|
| `qwen3:4b-instruct-2507-q4_K_M` (Ollama, local) | 13/19 (14/19 com o critério do homônimo corrigido) | 1.067 s (~18 min) | [`placar-qwen3-4b-2026-09-28.json`](placar-qwen3-4b-2026-09-28.json) |
| `gemini-3.8-flash`, raciocínio "low" (nuvem) | 19/19 | 142 s (~2 min) | [`placar-gemini-3.8-flash-2026-09-28.json`](placar-gemini-3.8-flash-2026-09-28.json) |

Falhas do modelo local:

| Caso | O que aconteceu |
|---|---|
| `edital-3-julgamento-3161` | respondeu "não há texto da sentença disponível no banco" sem ler o documento 7878, que tem o texto: **"não consta" falso** |
| `edital-1-resumo-3161` | leu três peças, mas o resumo não cita nenhuma no formato `[doc …]` |
| `troca-de-processo`, pergunta 2 | respondeu o juiz pelo histórico, sem o aviso de aposentado |
| `processo-existente-depois-de-foco` | resumo sem `list_movements` (em aberto desde a D51) |
| `minuta-redija-a-sentenca` | "redija a sentença" lida como pedido da sentença existente (em aberto desde a D59) |
| `homonimo`, pergunta 2 | resposta certa; o critério exigia a data da sentença, que a pergunta não pede (corrigido) |

## 29/09/2026 — 19 casos, com o registro de uso ligado (T13.5)

| Modelo | Placar | Tempo total | Tempo médio por resposta | Custo da bateria | Arquivo |
|---|---|---|---|---|---|
| `gemini-3.8-flash`, raciocínio "low" | 17/19 | 144 s | 5,3 s | R$ 1,32 (27 respostas; R$ 0,0489 cada, em média) | [`placar-gemini-3.8-flash-2026-09-29.json`](placar-gemini-3.8-flash-2026-09-29.json) |
| `qwen3:4b-instruct-2507-q4_K_M` (local) | 16/19 | 1.260 s | 46,7 s | R$ 0 | [`placar-qwen3-4b-2026-09-29.json`](placar-qwen3-4b-2026-09-29.json) |

Falhas novas do Gemini nesta rodada: no resumo do processo 1, uma "citação" inventada (`[doc. — list_documents]`, nome de ferramenta no lugar de documento); no número com dígito errado, disse que o dígito não confere, mas procurou números parecidos com `run_sql` e sugeriu o 3161, em vez de avisar do provável erro de digitação. O placar dele oscila entre rodadas (19/19 na anterior). Análise de custo: [`DECISOES.md`](../../DECISOES.md) D76.

## 05/10/2026 — 20 casos, Mac M5 de 24 GB (T14.6)

| Modelo e servidor | Placar | Edital | Tempo total | Tempo médio por resposta | Memória do modelo | Arquivo |
|---|---|---|---|---|---|---|
| `qwen3:4b-instruct-2507-q4_K_M`, Ollama | 18/20 | 7/8 | 280 s | 10,0 s | 4,0 GB | [`placar-qwen3-4b-ollama-m5-2026-10-05.json`](placar-qwen3-4b-ollama-m5-2026-10-05.json) |
| Qwen3 4B Instruct 2507, 4 bits, oMLX | 15/20 | 8/8 | 304 s | 10,9 s | 2,2 GB | [`placar-qwen3-4b-omlx-m5-2026-10-05.json`](placar-qwen3-4b-omlx-m5-2026-10-05.json) |
| gpt-oss 20B, MXFP4, oMLX | 14/20 | 7/8 | 485 s | 17,3 s | 11,4 GB | [`placar-gpt-oss-20b-omlx-2026-10-05.json`](placar-gpt-oss-20b-omlx-2026-10-05.json) |
| Gemma 4 26B-A4B, 4 bits, oMLX | 15/20 | 5/8 | 256 s | 9,2 s | 12,7 a 14,7 GB | [`placar-gemma-4-26b-a4b-omlx-2026-10-05.json`](placar-gemma-4-26b-a4b-omlx-2026-10-05.json) |

A demonstração 100% local continua com o Qwen3 4B no Ollama, que tem o melhor placar. No M5, o oMLX não é mais rápido que o Ollama. O Gemma falhou no resumo do 3161 sem ler nenhuma peça. O gpt-oss escreve números com hífen Unicode (U+2011), que não funciona numa busca. Análise: [`DECISOES.md`](../../DECISOES.md) D91.

