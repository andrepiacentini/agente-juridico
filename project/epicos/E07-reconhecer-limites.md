# E07 — Reconhecer limites

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** diante de dado ausente ou contraditório, o agente diz o que não sabe, em vez de inventar.
**Por que é o épico que nunca pode ser cortado:** é requisito do edital e o banco foi construído para testá-lo (63% dos processos sem documentos, datas sem sentença, juízes ausentes, nomes repetidos).

Cada tarefa = uma regra nas instruções do agente + uma verificação com pergunta real.

---

### T7.1 — Processo sem documentos `[x]`
- **Objetivo:** "resuma o processo 1" responde só com o andamento e avisa que não há peças disponíveis.
- **Passos:** regra nas instruções; testar com o processo 1.
- **Pronto quando:** a resposta menciona explicitamente a ausência de documentos e não inventa fatos.
- **Depende de:** E05.

### T7.2 — Data de sentença sem o texto da sentença `[x]`
- **Objetivo:** "o processo 1 já foi julgado?" responde que consta data de sentença, mas os fundamentos não estão disponíveis.
- **Passos:** regra nas instruções usando o campo "julgamento" (T3.3); testar com o processo 1.
- **Pronto quando:** a resposta não inventa decisão nem fundamentos.
- **Depende de:** T3.3, E05.

### T7.3 — Magistrado ausente ou aposentado `[x]`
- **Objetivo:** reportar "magistrado não consta no cadastro" ou "magistrado consta como aposentado", sem deduzir outro nome.
- **Passos:** regra nas instruções usando os avisos da T3.4; testar com o 3161 e com um processo sem magistrado.
- **Pronto quando:** ambas as respostas reportam o aviso corretamente.
- **Depende de:** T3.4, E05.

### T7.4 — Nome com mais de uma pessoa `[x]`
- **Objetivo:** "quais os processos de <nome homônimo>?" leva o agente a listar as opções e perguntar qual.
- **Passos:** regra nas instruções usando a T3.10; testar com um homônimo conhecido.
- **Pronto quando:** o agente pede a escolha em vez de misturar os processos das pessoas.
- **Depende de:** T3.10, E05.

### T7.5 — Processo inexistente `[x]`
- **Objetivo:** um número que não está no banco gera "processo não encontrado", sem inventar conteúdo.
- **Passos:** testar com um número bem formado mas inexistente.
- **Pronto quando:** a resposta é curta e não traz dados de outro processo.
- **Depende de:** T3.1, E05.

### T7.6 — Limite de tentativas na consulta livre `[x]`
- **Objetivo:** depois de 2 erros seguidos no `consultar_sql`, o agente para e diz que não conseguiu.
- **Passos:** contar tentativas na sessão; na terceira, a ferramenta devolve "limite atingido, informe ao usuário".
- **Pronto quando:** teste sem IA confirma o bloqueio; pergunta real impossível termina com mensagem honesta.
- **Depende de:** E04, T5.1.

### T7.7 — Citação obrigatória da fonte `[x]`
- **Objetivo:** toda resposta com fato do processo traz a fonte no formato combinado.
- **Passos:** reforçar a regra nas instruções com um exemplo; revisar as respostas das tarefas anteriores. Caso observado na T5.5: resposta vinda do histórico ("E qual é o valor da causa?" → "R$ 3.796,73") saiu sem citação — a regra precisa valer também quando o dado já está na conversa. Caso da T5.6 (D40): dados do cadastro (partes, juiz, valor) não têm formato de citação nas instruções — criar um, como "[cadastro do processo]". Casos da T7.2 (D48): datas saíram como AAAA-MM-DD, apesar da regra 8, e o aviso veio rotulado "Warning:", em inglês. Caso da T7.3 (D49): a resposta expôs o nome interno do campo ("O campo 'judge' está vazio"). Casos da T7.4 (D50): **data errada** (09/11/2025 no lugar de 2025-11-17), provável falha do modelo ao converter a data; avaliar as ferramentas devolverem datas já em DD/MM/AAAA. Aviso inventado por conta própria ("arquivado, mas já foi julgado"), contra a regra 4. Polo rotulado como "processo ativo/passivo". Caso da T7.5 (D51): depois da nova tentativa do validador, o resumo chamou só `find_case`, sem andamento nem índice de documentos.
- **Pronto quando:** as respostas das T7.1 a T7.5 citam documento ou movimentação sempre que afirmam algo.
- **Depende de:** T7.1 a T7.5.

### T7.8 — Avisar número de processo com dígito errado (opcional) `[x]`
- **Opcional:** a tarefa não é exigida pelo edital; sem ela, um número digitado errado já resulta em "processo não encontrado" (T7.5).
- **Objetivo:** quando o número tem formato CNJ mas o dígito verificador não confere, o agente avisa que provavelmente houve erro de digitação, em vez de só dizer que o processo não existe.
- **Passos:** em `case_number.py`, função que confere o dígito verificador pelo cálculo módulo 97 do padrão CNJ (os 10.000 números do banco passam nessa conferência — verificado na T2.4); usar na resposta de processo inexistente; testar com o 3161 com um dígito trocado.
- **Pronto quando:** "resuma o 0000007-78.2023.8.99.9014" (dígito errado) gera o aviso de digitação, e um número válido que não está no banco continua gerando "não encontrado".
- **Depende de:** T2.4, T7.5.

### T7.9 — Filtro de busca sem nenhum valor correspondente `[x]`
- **Objetivo:** quando `search_cases` não acha nada porque um filtro não corresponde a nenhum valor do banco (ex.: `case_class='any'`), a ferramenta diz qual filtro e, quando são poucos, quais valores existem, em vez de só "Nenhum processo atende aos filtros".
- **Origem:** achado da T7.6 (D52): com a resposta genérica, o modelo concluiu "Não consta processo com valor da causa", o que é falso.
- **Passos:** conferir cada filtro sozinho quando o resultado vem vazio; listar os valores de classe, assunto, vara e situação; testar com "qual o percentil 90 do valor da causa por classe processual?".
- **Pronto quando:** teste sem IA confirma a mensagem; a pergunta real não termina mais em "não consta" falso.
- **Depende de:** T3.11.
