# E09 — Bateria de perguntas de avaliação

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** um conjunto fixo de perguntas com o que a resposta deve (e não deve) conter, e um comando que roda tudo e mostra o placar.
**Por que incluir (o edital diz que testes são opcionais):** ao mexer nas instruções do agente, é fácil consertar uma resposta e estragar outra. A bateria mostra isso em minutos.

---

### T9.1 — Formato do arquivo de perguntas `[x]`
- **Objetivo:** definir `tests/golden.yaml`: pergunta, processo, "deve conter", "não deve conter".
- **Passos:** escrever o formato com 1 exemplo comentado.
- **Pronto quando:** o formato está documentado no próprio arquivo.
- **Depende de:** nada.
- **Para explicar à banca:** "Cada pergunta tem critérios simples de verificação, legíveis por quem não programa."

### T9.2 — As 4 perguntas do edital nos 2 processos de referência `[x]`
- **Objetivo:** 8 casos: perguntas 1 a 4 para o 3161 e para o processo 1.
- **Passos:** escrever os critérios (ex.: processo 1 + minuta → deve conter "petição inicial" e não deve conter "JULGO").
- **Pronto quando:** 8 casos no arquivo.
- **Depende de:** T9.1.
- **Para explicar à banca:** "Testo as perguntas do edital no melhor e no pior caso do banco."

### T9.3 — Casos das armadilhas `[x]`
- **Objetivo:** ~5 casos: processo inexistente, sem magistrado, homônimo, troca de processo na conversa, pergunta impossível.
- **Passos:** reaproveitar os roteiros do E06 e do E07 (`docs/roteiros/`). Incluir as falhas que ficaram em aberto na D53: cartão do processo sem `[cadastro do processo]` (T7.4), resumo curto sem citação (T7.5) e rótulo "[warning: …]" (T7.1); o resumo raso depois da nova tentativa do validador (D51); e, da D55, a busca com filtro errado que o modelo não refaz; da D59, "redija a sentença do processo 1" lida como pedido da sentença existente.
- **Pronto quando:** os casos estão no arquivo.
- **Depende de:** T9.1, E07.
- **Para explicar à banca:** "Cada armadilha do banco tem um caso que prova que o agente não cai nela."

### T9.4 — Comando que roda a bateria `[x]`
- **Objetivo:** script que executa todas as perguntas e imprime acerto/erro por caso e o total.
- **Passos:** ler o YAML; rodar o agente; checar os critérios; opção para escolher o modelo.
- **Pronto quando:** o comando roda e mostra o placar.
- **Depende de:** T9.2, T9.3.
- **Para explicar à banca:** "Um comando só me diz se uma mudança melhorou ou piorou o agente."

### T9.5 — Placar dos dois modelos `[ ]`
- **Objetivo:** rodar a bateria com o modelo local (`qwen3:4b-instruct-2507-q4_K_M`) e com Claude e registrar o resultado.
- **Passos:** rodar; anotar placar, tempo total e principais falhas no `DECISOES.md`.
- **Pronto quando:** os dois placares estão registrados com data.
- **Depende de:** T9.4.
- **Para explicar à banca:** "Tenho números para dizer onde o modelo local é suficiente e onde o da nuvem faz diferença."
