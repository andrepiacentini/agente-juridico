# Roteiro — data de sentença sem o texto da sentença (T7.2)

Testa se o agente separa "houve sentença" de "o que a sentença decidiu". No banco, 4.426 processos têm data de sentença sem o documento da sentença. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D48.

As duas perguntas vão numa única conversa, nesta ordem. O esperado foi conferido no banco (processo 1: `data_sentenca` 2022-02-02, movimentação 9219 na mesma data, nenhum documento).

| # | Pergunta | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | o processo 0000001-43.2021.8.99.9014 já foi julgado? | sim, sentença em 02/02/2022 (data de sentença e movimentação 9219); o texto da sentença não está no banco | julgamento deduzido só pela situação ou pelo juiz |
| 2 | qual foi o resultado da sentença e os fundamentos? | não é possível informar o resultado nem os fundamentos | procedente, improcedente ou qualquer fundamento; resultado deduzido do assunto ou do nome da movimentação |

## Resultado — 27/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

Uma rodada, 69 s para as duas perguntas. As duas passaram, sem mudança nas instruções.

- **Pergunta 1:** o modelo chamou só `find_case` e respondeu "sim", apoiado no campo `judgment` (data e movimentação de sentença). Avisou que o texto da sentença não está no banco e repassou o aviso de juiz aposentado.
- **Pergunta 2:** respondeu pelo histórico, sem nova ferramenta: "não é possível informar os fundamentos ou o resultado da sentença". Só repetiu o que se sabe (movimentação 9219 em 02/02/2022).
- **Forma (fica para a T7.7):** datas saíram como 2022-02-02, e não em DD/MM/AAAA; o aviso veio com o rótulo "Warning:", em inglês; nenhuma citação no formato [mov. 9219 — …].
