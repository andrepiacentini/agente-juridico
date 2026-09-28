# Roteiro — filtro de busca sem nenhum valor correspondente (T7.9)

Testa se uma busca vazia por causa de um filtro errado deixa de virar "não consta" falso. Quando `search_cases` não acha nada, a ferramenta confere cada filtro sozinho e diz qual não corresponde a nenhum valor do banco, listando os valores que existem para classe, assunto, vara e situação. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D55.

| # | Pergunta | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | qual o percentil 90 do valor da causa por classe processual? | explicação de que o filtro usado não existe, ou o cálculo com números que batem com o banco | "não consta processo com valor da causa" (o banco tem 10.000 processos) |

## Resultado — 28/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

- **Antes (T7.6, D52):** o modelo chamou `search_cases(case_class='any', …)`, recebeu "Nenhum processo atende aos filtros" e concluiu "Não consta processo com valor da causa", o que é falso.
- **Depois, 2 rodadas (46 e 28 s):** a mesma chamada agora recebe "Não há classe com 'any' no banco. Classes que existem: …". Nas duas, o modelo explicou que a classe "any" não existe e listou as 11 classes reais. Não houve "não consta" falso sobre os processos.
- **O que ainda falta:** o modelo não refez a busca sem o filtro errado nem calculou o percentil, e a primeira rodada abriu com um "Não consta no banco" solto antes da explicação. A `search_cases` não calcula percentil; a resposta completa exigiria `run_sql`.
