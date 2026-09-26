# E03 — Ferramentas de consulta

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** as funções que o agente vai usar para consultar o banco, cada uma com um teste que roda **sem IA**.
**Por que importa:** o modelo só escolhe *qual* ferramenta chamar; quem garante que o dado está certo é o código da ferramenta. Por isso as armadilhas do banco são tratadas aqui, não no prompt.

Regra que vale para todas: ferramentas de listagem devolvem **dados resumidos** (ids, tipos, datas). Só `read_document` devolve texto completo.

Nomes em inglês (D19), com o nome conceitual do `plan.md` entre parênteses: `find_case` (buscar_processo), `list_parties` (listar_partes), `list_movements` (listar_movimentacoes), `list_documents` (listar_documentos), `read_document` (ler_documento), `search_text` (buscar_texto), `search_cases` (nova, T3.11). Todas ficam em `src/case_assistant/tools.py`, recebem a conexão aberta (não a abrem) e devolvem um dicionário; "não encontrado" é uma resposta, não um erro.

---

### T3.1 — `find_case`: dados básicos `[x]`
- **Objetivo:** dado um número, devolver classe, assunto, comarca, vara, magistrado, datas, valor da causa e quantidade de documentos e movimentações.
- **Passos:** consulta com `LEFT JOIN` em `unidade` e `magistrado` (1.044 processos não têm magistrado e não podem sumir); aceitar o número formatado, só com dígitos ou dentro de um texto (`extract_case_number`); devolver um dicionário pequeno (~440 caracteres no 3161); processo inexistente ou texto sem número devolvem aviso claro, não erro.
- **Pronto quando:** teste com o 3161 confere os campos; teste com número inexistente devolve "processo não encontrado".
- **Depende de:** T2.1, T2.4.
- **Para explicar à banca:** "É a primeira ferramenta que o agente chama: um cartão de identificação do processo."

### T3.2 — `find_case`: situação padronizada `[x]`
- **Objetivo:** tratar `Julgado` / `JULGADO` / `julgado` como a mesma coisa.
- **Passos:** normalizar com `LOWER(TRIM())` no SQL e devolver em minúsculas no campo `status`. O banco tem 4 situações (arquivado, em andamento, julgado, suspenso) escritas de 3 jeitos cada — 12 valores distintos que viram 4.
- **Pronto quando:** teste com o processo 1 (`julgado` minúsculo) devolve a situação padronizada.
- **Depende de:** T3.1.
- **Para explicar à banca:** "O banco escreve a mesma situação de três jeitos; padronizo no código para o modelo não se confundir."

### T3.3 — `find_case`: campo "julgamento" cruzando três sinais `[x]`
- **Objetivo:** responder "já foi julgado?" com base em três fontes: `data_sentenca`, movimentações de sentença (códigos 9219/9220/9221) e existência de documento do tipo Sentença.
- **Passos:** calcular os três sinais — documento de sentença conta os tipos `Sentença` e `Sentença Homologatória de Acordo` (só assim os números batem: 4.426 com data sem documento, 37 no inverso); devolver no campo `judgment` um resumo com os sinais presentes e ausentes, sem escolher um lado, mais a movimentação e o documento de sentença (para citação). No banco: 1.775 processos com os três sinais, 3.671 sem nenhum, 4.554 divergentes, em 7 combinações.
- **Pronto quando:** testes com o 3161 (três sinais batem) e com o processo 1 (data sem documento) dão respostas diferentes e corretas.
- **Depende de:** T3.1.
- **Para explicar à banca:** "Em 4.426 processos há data de sentença sem a sentença. Por isso nunca confio num sinal só — o código cruza os três e entrega o resultado pronto."

### T3.4 — `find_case`: lista de inconsistências `[x]`
- **Objetivo:** avisar o agente sobre problemas no cadastro, sem corrigi-los.
- **Passos:** detectar: magistrado ausente (1.044), magistrado aposentado/removido (2.022), comarca do processo diferente da comarca da vara (1.024 — todas a mesma cidade grafada de outro jeito, reportadas como tal, D34), valor da causa vazio ou ≤ 0 (886), valor implausível — acima de 100 milhões, só o sentinela 9.999.999.999 (1 processo; acrescentado na reavaliação de cobertura, D36) —, conflito entre situação e data de sentença (43 "julgado" sem data), vara desativada (746, acrescentado a pedido do autor); devolver no campo `warnings` como lista de frases, calculada a partir do próprio cartão, sem consulta extra.
- **Pronto quando:** o 3161 devolve o aviso de juiz aposentado; um processo sem magistrado devolve o aviso correspondente.
- **Depende de:** T3.1.
- **Para explicar à banca:** "O agente reporta a inconsistência em vez de escolher um lado — num tribunal, esconder uma divergência é pior do que mostrá-la."

### T3.5 — `list_parties` `[x]`
- **Objetivo:** devolver as partes do processo por polo (ativo/passivo), com tipo e CPF/CNPJ.
- **Passos:** consulta em `processo_parte` + `parte`; agrupar por polo (`plaintiffs` = ativo, `defendants` = passivo); "tipo" = pessoa física/jurídica pelo formato do documento (CPF ou CNPJ), porque `parte.tipo` contradiz o polo em 1.633 vínculos (D35); mostrar uma vez só a parte vinculada duas vezes ao mesmo polo (99 casos), com aviso.
- **Pronto quando:** teste com o 3161 devolve autor(es) e réu(s) corretos.
- **Depende de:** T2.1.
- **Para explicar à banca:** "Partes estão em tabela própria; é uma consulta direta, sem interpretação."

### T3.6 — `list_movements` `[x]`
- **Objetivo:** devolver o andamento do processo em ordem de data.
- **Passos:** consulta em `movimentacao` ordenada por `data_mov` e, no mesmo dia, por `id`; só data, código e descrição (resposta média de ~1.100 caracteres, máximo ~2.000); movimentações repetidas no mesmo dia são mantidas como estão no banco; processo sem movimentação (3611) devolve lista vazia. Campo `warnings` (acrescentado a pedido do autor) destaca, para conferência humana, sequências incomuns: recurso de apelação depois do trânsito em julgado (220 processos — pode ser recurso fora do prazo ou erro de cadastro) e trânsito em julgado sem movimentação de sentença (16).
- **Pronto quando:** teste com o processo 1 devolve 16 movimentações em ordem.
- **Depende de:** T2.1.
- **Para explicar à banca:** "É o que permite resumir os 63% de processos que não têm nenhum documento."

### T3.7 — `list_documents` (sem texto) `[ ]`
- **Objetivo:** devolver a lista de documentos com id, tipo, autor, data e número de páginas — **sem o texto**.
- **Passos:** consulta em `documento` sem a coluna `texto`; marcar como advogado quem tem "OAB" no campo `autor`.
- **Pronto quando:** teste com o 3161 devolve 19 itens sem texto; teste com o processo 1 devolve lista vazia.
- **Depende de:** T2.1.
- **Para explicar à banca:** "O modelo primeiro vê o índice dos documentos e escolhe quais ler. É isso que faz caber num computador de 8 GB."

### T3.8 — `read_document` `[ ]`
- **Objetivo:** devolver o texto completo de um documento pelo id, com tipo e data para citação.
- **Passos:** consulta por `id`; id inexistente devolve aviso claro.
- **Pronto quando:** teste lê a sentença do 3161 e confere que o texto veio inteiro.
- **Depende de:** T2.1.
- **Para explicar à banca:** "Texto só é carregado quando o agente pede, e sempre com o id para ele citar a fonte."

### T3.9 — `search_text`: termos nos documentos `[ ]`
- **Objetivo:** encontrar documentos que mencionam um termo, com um trecho em volta.
- **Passos:** usar o índice da T2.5; filtros opcionais por tipo de documento e por processo; limitar a quantidade de resultados.
- **Pronto quando:** teste com "inversão do ônus" devolve documentos com id e trecho.
- **Depende de:** T2.5.
- **Para explicar à banca:** "Busca por palavra, não por 'significado parecido' — resolve o que o edital pede sem precisar de banco vetorial."

### T3.10 — `search_text`: nomes de partes e homônimos `[ ]`
- **Objetivo:** buscar uma pessoa pelo nome e separar pessoas diferentes com o mesmo nome.
- **Passos:** buscar no índice de `parte.nome`; agrupar resultados por CPF/CNPJ; sinalizar quando houver mais de uma pessoa.
- **Pronto quando:** teste com um nome homônimo conhecido devolve duas ou mais pessoas separadas, cada uma com seus processos.
- **Depende de:** T2.5.
- **Para explicar à banca:** "Há 643 nomes repetidos com documentos diferentes; a ferramenta separa as pessoas e o agente pergunta de qual se trata."

### T3.11 — `search_cases`: encontrar processos por atributo `[ ]`
- **Objetivo:** responder perguntas que selecionam processos por características — "quais processos são sobre plano de saúde?", "quantas execuções fiscais há em Joinville?", "quais processos o juiz X julgou?", "quais foram autuados em 2024 e ainda estão em andamento?", "qual o de maior valor?" — sem o modelo escrever SQL (D36).
- **Passos:** filtros opcionais e combináveis: assunto, classe, comarca, vara, nome do magistrado, situação (padronizada, T3.2), faixa de data de autuação, faixa de data de sentença, faixa de valor da causa; filtros de texto são "contém", sem diferença de acento e de maiúsculas (registrar uma função `unaccent` na conexão, em `db.py`, e reaproveitar a comparação de comarca da T3.4); ordenação por data de autuação, data de sentença ou valor; limite padrão 20 e máximo 50; devolver o **total** de processos que atendem aos filtros mais a lista compacta (número, classe, assunto, comarca, situação, data de autuação, valor); `LEFT JOIN` em magistrado e unidade (1.044 processos sem juiz); nenhum filtro informado devolve aviso pedindo ao menos um.
- **Pronto quando:** testes: "plano de saude" (sem acento) encontra os 444 processos de "Plano de Saúde — Negativa de Cobertura"; classe "execução fiscal" + comarca "joinville" bate com a contagem feita direto no SQL; o magistrado Luiz Bonetti Vasconcelos traz o 3161 entre os resultados; situação "em andamento" + autuação em 2024 bate com o SQL; o limite é respeitado e o total continua correto; sem filtro devolve o aviso.
- **Depende de:** T3.2, T3.4.
- **Para explicar à banca:** "As perguntas do edital são sobre um processo; mas 'quais processos…' é a pergunta mais provável fora da lista. Esta ferramenta responde isso com consultas prontas, e o SQL livre fica só para o que ninguém previu."
