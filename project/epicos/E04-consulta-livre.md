# E04 — Consulta livre protegida (`consultar_sql`)

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** uma ferramenta que deixa o agente escrever sua própria consulta SQL para perguntas imprevistas (ex.: "quantos processos essa vara tem?"), com várias travas de segurança.
**Por que importa:** as ferramentas do E03 cobrem as perguntas esperadas; esta é a "válvula de escape" para o resto. Ela é o ponto mais arriscado do sistema, então cada trava é uma tarefa separada e testada.

---

### T4.1 — Aceitar só consultas de leitura `[ ]`
- **Objetivo:** recusar qualquer comando que não seja `SELECT` ou `WITH`.
- **Passos:** validar o início do comando; recusar `;` (vários comandos), `PRAGMA` e `ATTACH`; devolver motivo da recusa.
- **Pronto quando:** `SELECT` passa; `DROP`, `DELETE`, `PRAGMA` e `SELECT 1; DROP ...` são recusados.
- **Depende de:** T2.1.
- **Para explicar à banca:** "São duas camadas: a validação recusa o comando e, se algo escapar, a conexão somente leitura barra."

### T4.2 — Limite de linhas `[ ]`
- **Objetivo:** nunca devolver mais de 50 linhas ao modelo.
- **Passos:** envolver a consulta em `SELECT * FROM (...) LIMIT 50`; avisar quando o resultado foi cortado.
- **Pronto quando:** `SELECT * FROM movimentacao` devolve 50 linhas e o aviso de corte.
- **Depende de:** T4.1.
- **Para explicar à banca:** "Uma consulta mal feita não pode despejar 134 mil linhas no modelo e travar a máquina."

### T4.3 — Tempo máximo de execução `[ ]`
- **Objetivo:** interromper consultas que demorem mais de 5 segundos.
- **Passos:** usar `set_progress_handler` do `sqlite3` para cancelar após o tempo; devolver aviso.
- **Pronto quando:** uma consulta propositalmente lenta (produto cartesiano) é interrompida e o teste passa.
- **Depende de:** T4.1.
- **Para explicar à banca:** "Mesmo uma consulta válida pode ser pesada demais; há um cronômetro que a corta."

### T4.4 — Erro vira informação para o modelo `[ ]`
- **Objetivo:** quando a consulta falha (coluna errada, sintaxe), devolver a mensagem de erro como texto, não quebrar o programa.
- **Passos:** capturar a exceção; devolver "erro: <mensagem do SQLite>" com uma dica do nome das tabelas.
- **Pronto quando:** consulta com coluna inexistente devolve texto de erro legível.
- **Depende de:** T4.1.
- **Para explicar à banca:** "Quando o agente erra, ele lê o erro e pode corrigir — é assim que ele aprende dentro da própria conversa."

### T4.5 — Descrição do banco para o modelo `[ ]`
- **Objetivo:** um texto curto com tabelas, colunas e as armadilhas conhecidas, para o modelo escrever SQL correto.
- **Passos:** escrever em `prompts.py` a descrição das 7 tabelas, com notas como "use `LOWER(situacao)`" e "datas são texto AAAA-MM-DD".
- **Pronto quando:** o texto tem menos de ~800 tokens e cobre todas as colunas.
- **Depende de:** nada (só leitura do `plan.md` §2).
- **Para explicar à banca:** "O modelo recebe o mapa do banco com os avisos das armadilhas já escritos."
