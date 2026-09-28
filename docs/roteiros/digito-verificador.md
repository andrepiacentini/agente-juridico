# Roteiro — número de processo com dígito errado (T7.8)

Testa se o agente separa "você digitou errado" de "esse processo não existe", usando os dígitos verificadores do número CNJ (módulo 97). Os 10.000 números do banco passam na conferência. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D54.

Cada pergunta vai numa conversa nova.

| # | Pergunta | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | resuma o 0000007-78.2023.8.99.9014 (o 3161 com o dígito 79 trocado por 78) | não encontrado; o dígito verificador (78) não confere; provável erro de digitação | dados do 3161 ou de outro processo; "com o usuário" (instrução ao modelo repassada) |
| 2 | resuma o processo 0000999-40.2023.8.99.9014 (dígito certo, fora do banco) | não consta no banco | aviso de erro de digitação |

## Resultado — 28/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

- **Pergunta 1, primeira rodada (34 s):** aviso certo, mas o modelo repassou ao usuário a frase do fim da mensagem, "Confirme o número com o usuário", escrita para ele. A frase foi trocada por "Confira o número do processo."
- **Pergunta 1, depois da troca (32 s):** "Não consta no banco. O dígito verificador (78) não confere com o restante do número: provavelmente houve erro de digitação. Confira o número do processo."
- **Pergunta 2 (7 s):** "Não consta no banco o processo 0000999-40.2023.8.99.9014.", sem aviso de digitação.
