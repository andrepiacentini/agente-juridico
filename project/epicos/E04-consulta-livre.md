# E04 — Consulta livre protegida (`run_sql`)

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** uma ferramenta que deixa o agente escrever sua própria consulta SQL para perguntas imprevistas (ex.: "quantos processos essa vara tem?"), com várias travas de segurança.
**Por que importa:** as ferramentas do E03 cobrem as perguntas esperadas; esta é a "válvula de escape" para o resto. Ela é o ponto mais arriscado do sistema, então cada trava é uma tarefa separada e testada.

---

### T4.1 — Aceitar só consultas de leitura `[x]`
- **Objetivo:** recusar qualquer comando que não seja `SELECT` ou `WITH`.
- **Passos:** em `src/case_assistant/sql_query.py`, `run_sql`: validar que é um único comando começando por `SELECT`/`WITH`, sem palavras de escrita ou administração (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `PRAGMA`, `ATTACH`, `DETACH`, `VACUUM`, `REINDEX`) fora de textos entre aspas; aceitar um `;` final; devolver o motivo da recusa. Terceira camada (D39): autorizador do SQLite ativo só durante a consulta, permitindo apenas leitura e funções — com uma única exceção, o `PRAGMA data_version` que o índice de busca faz internamente.
- **Pronto quando:** `SELECT` passa; `DROP`, `DELETE`, `PRAGMA` e `SELECT 1; DROP ...` são recusados.
- **Depende de:** T2.1.
- **Para explicar à banca:** "São três camadas: a validação recusa o comando; se algo escapar, o próprio SQLite nega qualquer operação que não seja leitura; e, por baixo de tudo, a conexão é somente leitura."

### T4.2 — Limite de linhas `[x]`
- **Objetivo:** nunca devolver mais de 50 linhas ao modelo.
- **Passos:** ler do cursor no máximo 51 linhas (`fetchmany`) — a 51ª só indica que houve corte; o SQL do modelo não é reescrito (`WITH` e `ORDER BY` continuam valendo) e o banco para de ler ali; avisar quando o resultado foi cortado. Dois limites a mais, porque 50 linhas não bastam para proteger o modelo: textos com mais de 300 caracteres são encurtados (com indicação de usar `read_document`), e o resultado inteiro não passa de ~6.000 caracteres (~2 mil tokens) — `SELECT texto FROM documento` cairia de ~19 mil para ~5.900 caracteres.
- **Pronto quando:** `SELECT * FROM movimentacao` devolve 50 linhas e o aviso de corte; consultas de texto longo respeitam o limite de tamanho, com aviso próprio.
- **Depende de:** T4.1.
- **Para explicar à banca:** "Uma consulta mal feita não pode despejar 134 mil linhas no modelo e travar a máquina."

### T4.3 — Tempo máximo de execução `[x]`
- **Objetivo:** interromper consultas que demorem mais de 5 segundos.
- **Passos:** usar `set_progress_handler` do `sqlite3` (conferido a cada 10 mil instruções) para cancelar após o tempo; devolver aviso. O cronômetro cobre a execução **e** a leitura das linhas: o SQLite só trabalha à medida que as linhas são lidas — em `SELECT 1 UNION ALL <produto cartesiano>`, o `execute` volta em ~2 ms e todo o peso fica na leitura. Limite de 5 s, parâmetro só de código (o modelo não o controla).
- **Pronto quando:** uma consulta propositalmente lenta (produto cartesiano) é interrompida e o teste passa.
- **Depende de:** T4.1.
- **Para explicar à banca:** "Mesmo uma consulta válida pode ser pesada demais; há um cronômetro que a corta."

### T4.4 — Erro vira informação para o modelo `[x]`
- **Objetivo:** quando a consulta falha (coluna errada, sintaxe), devolver a mensagem de erro como texto, não quebrar o programa.
- **Passos:** capturar a exceção; devolver "Erro na consulta: <mensagem do SQLite>" e, em `schema_hint`, todas as tabelas com suas colunas (~450 caracteres) para o modelo corrigir sozinho. Recusa (T4.1) e interrupção por tempo (T4.3) mantêm mensagens próprias. O teto de tentativas é do agente (T7.6).
- **Pronto quando:** consulta com coluna inexistente devolve texto de erro legível.
- **Depende de:** T4.1.
- **Para explicar à banca:** "Quando o agente erra, ele lê o erro e pode corrigir — é assim que ele aprende dentro da própria conversa."

### T4.5 — Descrição do banco para o modelo `[ ]`
- **Objetivo:** um texto curto com tabelas, colunas e as armadilhas conhecidas, para o modelo escrever SQL correto.
- **Passos:** escrever em `prompts.py` a descrição das 7 tabelas, com notas como "use `LOWER(situacao)`" e "datas são texto AAAA-MM-DD".
- **Pronto quando:** o texto tem menos de ~800 tokens e cobre todas as colunas.
- **Depende de:** nada (só leitura do `plan.md` §2).
- **Para explicar à banca:** "O modelo recebe o mapa do banco com os avisos das armadilhas já escritos."
