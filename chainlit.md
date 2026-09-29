# Assistente de processos — Desafio TJSC

Chat que responde, em português, perguntas sobre os processos judiciais **fictícios** do banco `desafio.sqlite`. O agente decide sozinho o que consultar, cita de onde tirou cada informação e diz quando o dado não está no banco.

## O que ele faz

- **Resume** um processo pelo número (ex.: `0000007-79.2023.8.99.9014`), com fatos, pedidos, defesa, andamento e resultado.
- **Mostra** partes, magistrado e advogados, e aponta inconsistências do cadastro (juiz aposentado, comarca grafada de outro jeito, nomes repetidos).
- **Responde** se o processo foi julgado, com a decisão e os fundamentos quando o texto da sentença está no banco.
- **Propõe** uma minuta de sentença, sempre marcada como **PROPOSTA DE MINUTA — texto não proferido**, e recusa quando faltam a petição inicial e a contestação.

Depois da primeira pergunta sobre um processo, as seguintes podem omitir o número ("e quem é o juiz?").

## Como conferir

As consultas ao banco aparecem logo abaixo da resposta, em "Consultou o banco de dados". Abra cada passo para ver o que o agente pediu e o que o banco devolveu. As citações seguem o formato `[doc 7878 — Sentença, 18/02/2026]`, `[mov. 9219 — …]` ou `[cadastro do processo]`.

## Limites

- O banco é **somente leitura** e **sintético**: nomes, números e documentos são fictícios.
- 63% dos processos não têm nenhum documento: nesses, o resumo sai só pelo andamento.
- O modelo pode errar. As respostas indicam as fontes para que possam ser conferidas.

A engrenagem ao lado do campo de mensagem troca o modelo (local ou em nuvem), sem perder a conversa.
