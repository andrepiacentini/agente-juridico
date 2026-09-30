# Roadmap — Agente de IA sobre dados estruturados (Desafio TJSC)

> Criado em 22/09/2026. Documento vivo: ajustar à medida que o projeto avança.
> Arquitetura e justificativas técnicas: [`plan.md`](../docs/plan.md). Decisões em linha do tempo: [`DECISOES.md`](../DECISOES.md). Termos técnicos: [`docs/glossario.md`](../docs/glossario.md).

## Objetivo final

Um chat em português, rodando no computador do autor, que responde perguntas sobre os processos do arquivo `desafio.sqlite`, **mostrando de onde tirou cada informação** e **dizendo claramente quando a informação não existe**. Deve responder às 4 perguntas do desafio técnico (resumo, partes/advogados/pedidos, julgamento, minuta de sentença) e manter o assunto entre uma pergunta e outra.

## Como este planejamento está organizado

- **Épico** = um bloco grande de trabalho com um resultado que dá para mostrar (ex.: "o agente já conversa no terminal").
- **Tarefa** = um passo pequeno, com começo, meio e fim, que cabe em uma sessão curta de trabalho e se explica em uma frase.

Cada tarefa tem sempre os mesmos campos:

| Campo | Para que serve |
|---|---|
| **Objetivo** | O que a tarefa entrega, em uma frase |
| **Passos** | O "meio": o que fazer, na ordem |
| **Pronto quando** | O "fim": como provar que terminou |
| **Depende de** | O que precisa estar pronto antes |

Legenda de situação: `[ ]` a fazer · `[~]` em andamento · `[x]` concluída · `[-]` cancelada (explicar no `DECISOES.md`).

## Épicos

| # | Épico | Resultado visível | Tarefas | Situação |
|---|---|---|---|---|
| E01 | [Preparação do ambiente](epicos/E01-preparacao-ambiente.md) | Projeto instala e roda com um comando | 11 | `[~]` |
| E02 | [Acesso seguro ao banco](epicos/E02-acesso-banco.md) | Conexão que só lê, provada por teste | 5 | `[x]` |
| E03 | [Ferramentas de consulta](epicos/E03-ferramentas-consulta.md) | 8 funções que respondem sobre um processo, testadas sem IA | 11 | `[x]` |
| E04 | [Consulta livre protegida](epicos/E04-consulta-livre.md) | "Válvula de escape" SQL que não consegue estragar nada | 5 | `[x]` |
| E05 | [Agente no terminal](epicos/E05-agente-terminal.md) | Conversa no terminal usando as ferramentas | 9 | `[x]` |
| E06 | [Memória da conversa](epicos/E06-memoria-conversa.md) | "E quem é o juiz?" funciona sem repetir o número | 4 | `[x]` |
| E07 | [Reconhecer limites](epicos/E07-reconhecer-limites.md) | O agente diz "não consta" em vez de inventar | 9 | `[x]` |
| E08 | [Minuta de sentença](epicos/E08-minuta-sentenca.md) | Minuta rotulada como proposta, ou recusa explicada | 5 | `[x]` |
| E09 | [Bateria de perguntas de avaliação](epicos/E09-avaliacao.md) | Placar de acertos por modelo | 5 | `[x]` |
| E10 | [Interface web](epicos/E10-interface-web.md) | Chat no navegador mostrando cada consulta feita | 4 | `[x]` |
| E11 | [Ajuste do modelo local](epicos/E11-ajuste-modelo-local.md) | Tempo e memória do modelo local medidos, como plano B | 6 | `[x]` |
| E12 | [Entrega e apresentação](epicos/E12-entrega-apresentacao.md) | README, roteiro da demo e respostas da arguição | 7 | `[x]` |
| E13 | [Consumo e custo](epicos/E13-consumo-custo.md) | Custo por resposta e painel de consumo no chat, com projeção | 5 | `[x]` |
| E14 | [Melhorias de uso](epicos/E14-melhorias-de-uso.md) | Ajustes que o uso frequente levanta: identidade visual, instalação em outros sistemas | 2 | `[ ]` |

**Total: 87 tarefas.**

## Ordem e dependências

```
E01 ──> E02 ──> E03 ──┬──> E05 ──> E06 ──> E07 ──> E08 ──> E09 ──> E12
                      │                                       ▲
                      └──> E04 ──────────> (entra no E05) ────┤
                                                              │
                             E10 (depois do E05) ─────────────┤
                             E13 (depois do E10) ─────────────┤
                             E11 (depois do E09) ─────────────┘
                             E14 (depois do E12, contínuo)
```

- **E01 a E04 não dependem de IA nenhuma.** São a base que justifica a arquitetura e podem ser testados e demonstrados sozinhos.
- **Ordem a partir do E10 (D71):** E13 (a medição de consumo alimenta a decisão de custo), depois o E11 enxuto, depois o E12.

## Processos de referência (usados em várias tarefas)

- **3161** — `0000007-79.2023.8.99.9014`: processo "rico", 19 documentos, sentença parcialmente procedente, juiz aposentado.
- **1** — `0000001-43.2021.8.99.9014`: processo sem nenhum documento, situação escrita `julgado` em minúsculas, tem data de sentença.
