# Roteiro — minuta de sentença do processo 3161 (T8.5)

Pergunta 4 do edital no melhor caso do banco: o 3161 (`0000007-79.2023.8.99.9014`) tem petição inicial e contestação. Testa se a minuta sai com o aviso, na estrutura de sentença, baseada só nas peças lidas e sem copiar a sentença existente. A bateria de avaliação reaproveita este roteiro (T9.2). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D60. As duas minutas geradas estão em [`saidas/`](saidas/).

**Pedido:** elabore uma minuta de sentença para o processo 0000007-79.2023.8.99.9014

| Deve conter | Não deve conter |
|---|---|
| "PROPOSTA DE MINUTA — texto não proferido" na primeira linha | leitura do doc 7878 (sentença existente) |
| RELATÓRIO, FUNDAMENTAÇÃO e DISPOSITIVO | lei, artigo ou jurisprudência fora das peças (as peças citam só o art. 28 do CTB e o art. 341 do CPC) |
| partes: João Ziegler Rocha × Operadora de Saúde Cambirela Ltda | fato que não esteja nas peças |
| pedido de indenização a arbitrar; valor da causa R$ 3.796,73 | dispositivo que contradiga a fundamentação |
| defesa: inépcia e valor excessivo; inépcia afastada no saneamento | assinatura, juiz, data ou local |
| aviso de que o conteúdo da prova oral (gravada) não está nas peças | |
| citação `[doc …]` dos fatos | |

Peças que o modelo deve ler (vêm de `prepare_draft`): 7865 Petição Inicial, 7868 Contestação, 7869 Réplica, 7870 Decisão de Saneamento, 7875 Ata de Audiência.

## Resultado — 28/09/2026, uma rodada em cada modelo

| Critério | `qwen3:4b-instruct-2507-q4_K_M` (Ollama) | `gemini-3.8-flash` (raciocínio "low") |
|---|---|---|
| Tempo | 187 s | 11 s |
| Aviso, três seções, 5 peças lidas, sentença não lida | sim | sim |
| Citações `[doc …]` conferem | sim | sim |
| Lei fora das peças | nenhuma | nenhuma |
| Prova oral indisponível | não menciona | menciona (depoimentos gravados e boletim de ocorrência não estão nas peças) |
| Fundamentação | dá o nexo causal como "demonstrado" citando a própria petição; adota "valor excessivo" da ré sem análise | preliminar e mérito separados; apoia-se na falta de impugnação específica da dinâmica do acidente (art. 341 do CPC, citado na réplica) |
| Dispositivo | **contraditório**: parcialmente procedente, custas para a ré e, duas linhas depois, sucumbência para o autor "pela falha na alegação de dano real"; julga "procedentes" a citação e a produção de provas | coerente: procedente, R$ 3.796,73, custas e honorários pela ré |
| Português | erros ("requérda", "deferiada"; "a autora") | correto |
| **Aceitável** | **não** | **sim** |

A sentença real do processo (doc 7878) é "parcialmente procedente"; a minuta do Gemini chega a "procedente". Para uma proposta feita só a partir das peças, sem o conteúdo da prova oral, é um resultado defensável, e ela diz de onde tirou cada ponto.
