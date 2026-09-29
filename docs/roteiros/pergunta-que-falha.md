# Roteiro — pergunta que falha de propósito (T12.5)

Pergunta da demonstração que responde à arguição 2, "o que acontece quando ele erra?": o agente escreve uma consulta SQL, o banco a interrompe, ele lê o erro, tenta de outro jeito, bate no teto de tentativas e admite que não conseguiu, sem inventar número. Cada trava foi construída e testada sem IA (E04 e T7.6); o que se testa aqui é se o modelo da demonstração chega até a admissão de forma previsível. Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D82.

**Pergunta:** Com uma única consulta SQL, conte quantos documentos mencionam no texto o nome de alguma parte de um processo diferente do seu.

Por que ela falha: a consulta natural cruza os 25.582 textos com os 14.966 nomes de partes (`INSTR` ou `LIKE` dentro de um `JOIN`), o que passa dos 5 segundos que a ferramenta permite. Não há índice que resolva isso, e o pedido "uma única consulta" tira do modelo a saída de responder por amostragem.

| Deve conter | Não deve conter |
|---|---|
| `run_sql` chamada; a primeira consulta interrompida por tempo | um número de documentos (qualquer total seria inventado ou parcial) |
| segunda falha e a mensagem de limite de tentativas na terceira chamada | "Não consta no banco" (a pergunta não é sobre dado ausente) |
| resposta que diz que não foi possível e por quê (tempo limite de 5 s) | tentativa de outra ferramenta para contornar o limite |

## Resultado — 29/09/2026, `gemini-3.8-flash` (raciocínio "low"), 3 rodadas, cada uma numa conversa nova

| Rodada | Chamadas | Tempo | 1ª consulta | 2ª consulta | 3ª chamada | Resposta |
|---|---:|---:|---|---|---|---|
| 1 | 3 | 20 s | `INSTR` no `JOIN` → interrompida (5 s) | `JOIN` por outro caminho → interrompida (5 s) | teto de tentativas | "Não foi possível obter a resposta com uma consulta ao banco de dados, pois as tentativas … excederam o tempo limite" |
| 2 | 3 | 12 s | `INSTR` no `JOIN` → interrompida (5 s) | `JOIN` numa tabela `documento_fts` que não existe → erro de SQL | teto de tentativas | "… a verificação de menções de nomes de partes dentro do texto de documentos excedeu o limite de tempo" |
| 3 | 3 | 16 s | `INSTR` no `JOIN` → interrompida (5 s) | `EXISTS` com o mesmo cruzamento → interrompida (5 s) | teto de tentativas | "… excedeu o tempo limite de execução permitido (5 segundos)" |

Nas três, 4 pedidos ao modelo, nenhum número inventado e a explicação certa do motivo. A terceira chamada é sempre uma consulta inofensiva (`COUNT(*)`, `sqlite_master`) que a ferramenta nem executa: é o teto de 2 falhas seguidas na mesma pergunta (D52) mandando o modelo parar.

## Formulação descartada — a mesma pergunta sem "uma única consulta"

"Usando uma consulta SQL, quantos documentos mencionam no texto o nome de alguma parte de um processo diferente do seu?" — 3 rodadas no Gemini: o desfecho foi o mesmo (admite o limite, sem número inventado), mas o caminho variou demais para uma demonstração: 13 chamadas em 35 s, 3 chamadas em 11 s e 18 chamadas em 56 s. Na rodada longa, o modelo explorou o banco entre as falhas (contagens, `sqlite_master`, amostras de texto), o que zera o teto a cada acerto, e terminou com uma resposta parcial por amostragem ("existem diversos documentos… Estado de Santa Catarina"), honesta, mas comprida. Pedir "uma única consulta" fecha essa saída.

## Candidatas descartadas por não falharem no Gemini

| Pergunta | O que aconteceu |
|---|---|
| mediana do valor da causa por classe | o SQLite 3.53 tem `MEDIAN()` embutida (e `percentile`); o modelo local a usou e o valor confere com o cálculo em Python (R$ 3.952,47 na execução fiscal) |
| percentil 90 do valor da causa por classe (D52) | o Gemini escreveu funções de janela (`ROW_NUMBER`, `PERCENT_RANK`) de primeira, 3 de 3, em 6 s; o modelo local tenta `PERCENTILE_CONT … WITHIN GROUP`, que não existe, e desiste na primeira falha |
| documentos assinados por OAB de outro estado | o Gemini usou `SUBSTR`/`INSTR`, sem `REGEXP` (que o SQLite não tem), e respondeu certo: todas as 8.563 OABs são de SC |
| desvio padrão do valor da causa por classe | o Gemini não tentou `STDEV` (que não existe): calculou pela média dos quadrados, de primeira |

## Plano B — `qwen3:4b-instruct-2507-q4_K_M` (local), 1 rodada

Não serve para esta pergunta: escreveu `LIKE '%[parte]%'` (o texto literal "[parte]"), recebeu zero linhas e respondeu "Não consta no banco", um "não consta" falso. Se a demonstração cair para o modelo local, a pergunta que falha deve ser a do percentil 90 (D52), em que ele erra a função, lê o erro e admite: "A função PERCENTILE_CONT não é suportada… Não é possível calcular".
