# Roteiro — processo sem documentos (T7.1)

Testa se o agente, diante de um processo sem nenhuma peça no banco (63% dos processos), resume só pelo cadastro e pelo andamento, diz com clareza que não há documentos e não inventa fatos a partir do assunto ou da classe. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D47.

Cada pergunta vai numa conversa nova. O esperado foi conferido no banco (processo 1: 0 documentos, 16 movimentações).

| # | Pergunta | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | resuma o processo 0000001-43.2021.8.99.9014 | aviso de que não há documentos; andamento de 11/01/2021 (Distribuição por Sorteio) a 05/04/2022 (Remessa à Instância Superior); sentença com resolução do mérito em 02/02/2022, sem o texto | fatos, pedidos ou fundamentos da causa; resultado da sentença (procedente/improcedente) |
| 2 | quais foram os pedidos do autor no processo 0000001-43.2021.8.99.9014? | não há petição inicial (nem outro documento) no banco | pedidos deduzidos do assunto "Rescisão Contratual c/c Perdas e Danos" |

## Resultado — 27/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

Uma rodada de cada pergunta. As duas passaram, sem mudança nas instruções.

- **Pergunta 1 (99 s):** o modelo chamou `find_case`, `list_movements` e `list_documents`. A resposta abre com "Não consta no banco nenhum documento" e fecha com "A sentença foi proferida, mas seu texto não está presente no sistema". O cadastro e as 16 movimentações conferem com o banco. Também repassou os dois avisos das ferramentas: juiz aposentado e apelação registrada depois do trânsito em julgado.
- **Pergunta 2 (19 s):** o modelo chamou `find_case` e `list_documents` e respondeu que, sem a petição inicial, não há informação sobre os pedidos. Não deduziu nada do assunto.
- **Citação:** nenhuma resposta cita as movimentações no formato combinado ([mov. 9219 — …]). Isso fica para a T7.7.
