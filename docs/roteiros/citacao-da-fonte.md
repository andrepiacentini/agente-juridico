# Roteiro — citação da fonte (T7.7)

Não tem perguntas próprias: reaproveita os roteiros das T7.1 a T7.5 e confere, em cada resposta com fato do processo, a citação no formato combinado e a forma da resposta. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D53.

Roteiros usados: [processo sem documentos](processo-sem-documentos.md) (T7.1), [sentença sem texto](sentenca-sem-texto.md) (T7.2), [magistrado ausente ou aposentado](magistrado-ausente-ou-aposentado.md) (T7.3), [nome com mais de uma pessoa](nome-com-mais-de-uma-pessoa.md) (T7.4) e [processo inexistente](processo-inexistente.md) (T7.5).

Em toda resposta com fato do processo:

| Deve conter | Não deve conter |
|---|---|
| citação copiada do campo `source`: `[doc 7878 — Sentença, 18/02/2026]`, `[mov. 9219 — Sentença com Resolução do Mérito, 18/02/2026]` ou `[cadastro do processo]` | datas em AAAA-MM-DD; data diferente da que a ferramenta devolveu |
| datas em DD/MM/AAAA e valores em reais | nomes de campos ("o campo 'judge'") ou rótulos em inglês ("Warning:") |
| partes como autor ou réu | avisos que nenhuma ferramenta deu; "processo ativo/passivo" no lugar de autor/réu |

## Resultado — 28/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

Uma rodada de cada roteiro, 9 conversas, depois das mudanças da D53.

- **Citação:** 5 das 7 respostas com fatos citam a fonte no formato combinado (T7.1 resumo, T7.2 nas duas perguntas, T7.3 nas duas, com `[cadastro do processo]`). O cartão do processo da T7.4 cita a movimentação de sentença, mas não o cadastro. O resumo curto da T7.5 (processo 1 depois do 3161) não cita nada e descreve a movimentação como "código 9219, data 02/02/2022".
- **Datas:** todas em DD/MM/AAAA e iguais às do banco, inclusive a da T7.4 (17/11/2025), que antes saiu errada.
- **Forma:** nenhum nome de campo, nenhum aviso inventado; na T7.4, "autor em processo…" e "réu em processo…". Sobrou um rótulo em inglês no resumo da T7.1: "[warning: Recurso de apelação…]".
- **Tempo:** resumo do processo 1 em 80 s (antes 99 s); conversa do homônimo em 54 s (antes 77 a 81 s).
