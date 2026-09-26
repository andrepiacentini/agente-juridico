# E02 — Acesso seguro ao banco

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** um único ponto do código (`db.py`) abre o banco, e está provado por teste que ele só consegue ler.
**Por que importa:** o agente vai gerar consultas sozinho; a garantia de que ele não altera nada precisa vir do próprio banco, não da boa vontade do modelo.

---

### T2.1 — Função de conexão somente leitura `[x]`
- **Objetivo:** `connect()` que abre `desafio.sqlite` apenas para leitura.
- **Passos:** usar `sqlite3.connect("file:desafio.sqlite?mode=ro", uri=True)`; caminho do banco configurável pela variável de ambiente `DATABASE_PATH`, com padrão na raiz do projeto; `row_factory = sqlite3.Row` para acessar colunas pelo nome; erro específico (`DatabaseNotFoundError`) se o arquivo não existir.
- **Pronto quando:** `connect()` executa `SELECT COUNT(*) FROM processo` e devolve 10.000.
- **Depende de:** T1.6.
- **Para explicar à banca:** "O banco é aberto em modo somente leitura pelo próprio SQLite — mesmo que o modelo tente apagar algo, o banco recusa."

### T2.2 — Teste: escrita é recusada `[x]`
- **Objetivo:** provar a garantia da T2.1.
- **Passos:** em `tests/test_db.py`, tentar `INSERT`, `UPDATE`, `DELETE`, `DROP TABLE` e `CREATE TABLE` e verificar que dá erro; confirmar que os dados continuam iguais depois das tentativas.
- **Pronto quando:** `uv run pytest tests/test_db.py` passa.
- **Depende de:** T2.1.
- **Para explicar à banca:** "Não confio só na regra: tenho um teste que tenta escrever e confirma que falha."

### T2.3 — Teste: o arquivo do banco não muda `[x]`
- **Objetivo:** garantir que nada do projeto altera `desafio.sqlite`.
- **Passos:** guarda automática em `tests/conftest.py` que compara o SHA-256 do arquivo com a referência da D27 no início e no fim de **toda** rodada de testes; teste explícito da referência; teste que altera um byte de uma cópia e confirma que o hash muda. Prova de que a guarda falha feita numa cópia isolada do projeto (D31).
- **Pronto quando:** o teste passa e falharia se o arquivo mudasse.
- **Depende de:** T2.1.
- **Para explicar à banca:** "Comparo a impressão digital do arquivo antes e depois — é a prova de que o dado original está intacto."

### T2.4 — Reconhecer e validar o número do processo `[ ]`
- **Objetivo:** função que acha um número no formato CNJ dentro de um texto e o padroniza.
- **Passos:** expressão regular para `NNNNNNN-DD.AAAA.J.TR.OOOO`; aceitar também o número só com dígitos (20 dígitos) e formatar; testar com o 3161 e com um número inexistente.
- **Pronto quando:** `extract_case_number("resuma o 0000007-79.2023.8.99.9014")` devolve o número, e texto sem número devolve `None`.
- **Depende de:** T1.6.
- **Para explicar à banca:** "O número do processo é a chave de tudo; reconheço ele por código, sem depender do modelo acertar a digitação."

### T2.5 — Índice de busca por palavras em área temporária `[ ]`
- **Objetivo:** permitir buscar termos no texto dos documentos e nos nomes das partes, sem alterar o arquivo.
- **Passos:** ao conectar, criar tabelas FTS5 em `TEMP` a partir de `documento.texto` e `parte.nome`; medir quanto tempo leva.
- **Pronto quando:** uma busca por "ônus da prova" retorna documentos, o teste da T2.3 continua passando e o tempo de criação está anotado.
- **Depende de:** T2.1, T2.3.
- **Para explicar à banca:** "A busca por palavras usa um recurso que já vem no SQLite, montado na memória a cada execução — sem servidor extra e sem tocar no arquivo."
