# E07 — Reconhecer limites

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** diante de dado ausente ou contraditório, o agente diz o que não sabe, em vez de inventar.
**Por que é o épico que nunca pode ser cortado:** é requisito do edital e o banco foi construído para testá-lo (63% dos processos sem documentos, datas sem sentença, juízes ausentes, nomes repetidos).

Cada tarefa = uma regra nas instruções do agente + uma verificação com pergunta real.

---

### T7.1 — Processo sem documentos `[ ]`
- **Objetivo:** "resuma o processo 1" responde só com o andamento e avisa que não há peças disponíveis.
- **Passos:** regra nas instruções; testar com o processo 1.
- **Pronto quando:** a resposta menciona explicitamente a ausência de documentos e não inventa fatos.
- **Depende de:** E05.
- **Para explicar à banca:** "Seis em cada dez processos não têm documentos; o agente resume pelo andamento e diz isso com clareza."

### T7.2 — Data de sentença sem o texto da sentença `[ ]`
- **Objetivo:** "o processo 1 já foi julgado?" responde que consta data de sentença, mas os fundamentos não estão disponíveis.
- **Passos:** regra nas instruções usando o campo "julgamento" (T3.3); testar com o processo 1.
- **Pronto quando:** a resposta não inventa decisão nem fundamentos.
- **Depende de:** T3.3, E05.
- **Para explicar à banca:** "Saber que houve sentença não é saber o que ela decidiu — o agente separa as duas coisas."

### T7.3 — Magistrado ausente ou aposentado `[ ]`
- **Objetivo:** reportar "magistrado não consta no cadastro" ou "magistrado consta como aposentado", sem deduzir outro nome.
- **Passos:** regra nas instruções usando os avisos da T3.4; testar com o 3161 e com um processo sem magistrado.
- **Pronto quando:** ambas as respostas reportam o aviso corretamente.
- **Depende de:** T3.4, E05.
- **Para explicar à banca:** "O agente mostra o que o cadastro diz, inclusive quando ele está incompleto."

### T7.4 — Nome com mais de uma pessoa `[ ]`
- **Objetivo:** "quais os processos de <nome homônimo>?" leva o agente a listar as opções e perguntar qual.
- **Passos:** regra nas instruções usando a T3.10; testar com um homônimo conhecido.
- **Pronto quando:** o agente pede a escolha em vez de misturar os processos das pessoas.
- **Depende de:** T3.10, E05.
- **Para explicar à banca:** "Misturar dados de duas pessoas com o mesmo nome seria um erro grave; o agente pergunta antes."

### T7.5 — Processo inexistente `[ ]`
- **Objetivo:** um número que não está no banco gera "processo não encontrado", sem inventar conteúdo.
- **Passos:** testar com um número bem formado mas inexistente.
- **Pronto quando:** a resposta é curta e não traz dados de outro processo.
- **Depende de:** T3.1, E05.
- **Para explicar à banca:** "Quando a consulta volta vazia, a resposta é 'não consta' — essa é a vantagem de consultar dados em vez de buscar textos parecidos."

### T7.6 — Limite de tentativas na consulta livre `[ ]`
- **Objetivo:** depois de 2 erros seguidos no `consultar_sql`, o agente para e diz que não conseguiu.
- **Passos:** contar tentativas na sessão; na terceira, a ferramenta devolve "limite atingido, informe ao usuário".
- **Pronto quando:** teste sem IA confirma o bloqueio; pergunta real impossível termina com mensagem honesta.
- **Depende de:** E04, T5.1.
- **Para explicar à banca:** "O agente pode errar e corrigir, mas não fica tentando para sempre — depois de duas falhas ele admite."

### T7.7 — Citação obrigatória da fonte `[ ]`
- **Objetivo:** toda resposta com fato do processo traz a fonte no formato combinado.
- **Passos:** reforçar a regra nas instruções com um exemplo; revisar as respostas das tarefas anteriores.
- **Pronto quando:** as respostas das T7.1 a T7.5 citam documento ou movimentação sempre que afirmam algo.
- **Depende de:** T7.1 a T7.5.
- **Para explicar à banca:** "Cada afirmação aponta de onde veio, para que a pessoa possa conferir no processo."

### T7.8 — Avisar número de processo com dígito errado (opcional) `[ ]`
- **Opcional:** a tarefa não é exigida pelo edital; sem ela, um número digitado errado já resulta em "processo não encontrado" (T7.5).
- **Objetivo:** quando o número tem formato CNJ mas o dígito verificador não confere, o agente avisa que provavelmente houve erro de digitação, em vez de só dizer que o processo não existe.
- **Passos:** em `case_number.py`, função que confere o dígito verificador pelo cálculo módulo 97 do padrão CNJ (os 10.000 números do banco passam nessa conferência — verificado na T2.4); usar na resposta de processo inexistente; testar com o 3161 com um dígito trocado.
- **Pronto quando:** "resuma o 0000007-78.2023.8.99.9014" (dígito errado) gera o aviso de digitação, e um número válido que não está no banco continua gerando "não encontrado".
- **Depende de:** T2.4, T7.5.
- **Para explicar à banca:** "O número do processo tem um dígito de conferência; uso ele para distinguir 'você digitou errado' de 'esse processo não existe'."
