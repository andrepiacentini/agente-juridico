# Roteiro — nome com mais de uma pessoa (T7.4)

Testa se o agente, diante de um nome que pertence a pessoas diferentes, lista as opções separadas por CPF/CNPJ e pergunta de qual se trata, em vez de misturar os processos. No banco, 643 nomes de parte se repetem com CPF diferente. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D50.

As duas perguntas vão numa única conversa, nesta ordem. O esperado foi conferido no banco. A busca acha as palavras do nome em qualquer posição, então "Adriana Bittencourt" traz 4 pessoas: 2 com esse nome exato e 2 com um nome do meio.

| # | Pergunta | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | quais os processos de Adriana Bittencourt? | as 4 pessoas, cada uma com o CPF e o processo: Adriana Ehlke Bittencourt (999.094.178-25, 0000005-41.2025.8.99.9014, ativo); Adriana Bittencourt (999.125.243-15, 0000018-16.2024.8.99.9001, ativo); Adriana Bittencourt (999.332.735-33, 0000027-05.2020.8.99.9005, passivo); Adriana Stahl Bittencourt (999.395.282-34, 0000098-82.2021.8.99.9001, passivo); pergunta de qual se trata | processos de pessoas diferentes atribuídos a uma só; "Pergunte de qual se trata" (instrução ao modelo repassada ao usuário) |
| 2 | a do CPF 999.125.243-15 | só o processo 0000018-16.2024.8.99.9001 (sentença em 17/11/2025, sem o texto no banco) | processos das outras três pessoas; data de sentença diferente de 17/11/2025 |

## Resultado — 28/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

Duas rodadas: uma antes e outra depois de mudar o texto do aviso de homônimo (D50).

- **Rodada 1, pergunta 1:** as 4 pessoas certas, separadas por CPF. Mas o modelo repassou ao usuário o aviso da ferramenta tal como veio, "Pergunte de qual se trata antes de responder", e não fez pergunta nenhuma.
- **Rodada 1, pergunta 2 (81 s no total):** o processo certo, mas com um aviso que nenhuma ferramenta deu: "O processo está arquivado, mas já foi julgado por sentença".
- **Rodada 2, pergunta 1:** com o aviso reescrito, a resposta abre com "Encontrei 4 pessoas diferentes com esse nome (CPF/CNPJ distintos). De qual delas se trata?" e lista as 4. Rotulou o polo como "processo ativo"/"processo passivo", o que pode ser lido como situação do processo.
- **Rodada 2, pergunta 2 (77 s no total):** o processo certo, sem o aviso inventado, mas com a data da movimentação de sentença errada: **09/11/2025**, quando a ferramenta devolveu 2025-11-17.
