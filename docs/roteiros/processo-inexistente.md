# Roteiro — processo inexistente (T7.5)

Testa se o agente responde "não consta" para um número que não está no banco, sem inventar conteúdo nem trazer dados de outro processo, e se só afirma isso depois de consultar. O número de teste, `0000999-40.2023.8.99.9014`, tem o formato CNJ e o dígito verificador certo (a conta dá 79 no 3161, como no banco), mas não existe no banco. O caso do dígito errado é outro (T7.8). A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D51.

As conversas 2 e 3 começam com um processo em foco: é a armadilha. O número novo não muda o foco, e um modelo que não consulta pode responder sobre o processo anterior ou dizer "não consta" sem ter olhado.

| # | Conversa | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | "resuma o processo 0000999-40.2023.8.99.9014" | `find_case` com esse número; "não consta" | qualquer dado de processo |
| 2 | "qual o assunto do processo 0000007-79.2023.8.99.9014?" → "resuma o processo 0000999-40.2023.8.99.9014" | no 2º turno, `find_case` com o número novo; "não consta" | Acidente de Trânsito, João Ziegler Rocha, R$ 3.796,73 (dados do 3161) |
| 3 (controle) | "qual o assunto do processo 0000007-79.2023.8.99.9014?" → "resuma o processo 0000001-43.2021.8.99.9014" | no 2º turno, `find_case` com o processo 1; resumo com Rescisão Contratual c/c Perdas e Danos | "não consta" (o processo 1 existe) |

## Resultado — 28/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

- **Conversa 1:** passou nas 2 rodadas (9 e 40 s), com `find_case` e "Não consta no banco o processo…".
- **Conversa 2, sem guarda:** 3 de 3 rodadas **sem nenhuma ferramenta** no 2º turno; a resposta "não consta" saiu certa por acaso. Com uma regra a mais nas instruções, 2 de 2 falharam igual, e uma delas ainda afirmou "Foi consultado com find_case()".
- **Conversa 3, sem guarda:** 2 de 2 rodadas disseram "Não consta no banco o processo 0000001-43.2021.8.99.9014" **sem consultar**. É falso: o processo existe.
- **Com o guarda da resposta (D51):** conversa 2 com `find_case(0000999-40…)` e "não consta" (34 s no total); conversa 3 com `find_case(0000001-43…)` e resumo com os dados certos (91 s no total).
- **Para a T7.7 e a bateria:** o resumo da conversa 3 com guarda chamou só `find_case`, sem `list_movements` nem `list_documents`. Por isso não lista o andamento e diz só que falta a sentença, não que o processo não tem documentos.
