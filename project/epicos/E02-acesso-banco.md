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

### T2.2 — Teste: escrita é recusada `[x]`
- **Objetivo:** provar a garantia da T2.1.
- **Passos:** em `tests/test_db.py`, tentar `INSERT`, `UPDATE`, `DELETE`, `DROP TABLE` e `CREATE TABLE` e verificar que dá erro; confirmar que os dados continuam iguais depois das tentativas.
- **Pronto quando:** `uv run pytest tests/test_db.py` passa.
- **Depende de:** T2.1.

### T2.3 — Teste: o arquivo do banco não muda `[x]`
- **Objetivo:** garantir que nada do projeto altera `desafio.sqlite`.
- **Passos:** guarda automática em `tests/conftest.py` que compara o SHA-256 do arquivo com a referência da D27 no início e no fim de **toda** rodada de testes; teste explícito da referência; teste que altera um byte de uma cópia e confirma que o hash muda. Prova de que a guarda falha feita numa cópia isolada do projeto (D31).
- **Pronto quando:** o teste passa e falharia se o arquivo mudasse.
- **Depende de:** T2.1.

### T2.4 — Reconhecer e validar o número do processo `[x]`
- **Objetivo:** função que acha um número no formato CNJ dentro de um texto e o padroniza.
- **Passos:** em `src/case_assistant/case_number.py`, expressão regular para `NNNNNNN-DD.AAAA.J.TR.OOOO`; aceitar também o número só com dígitos (20 dígitos) e formatar; testar com o 3161, com um número bem formado que não existe no banco (a existência é conferida pelas ferramentas, no E03) e com os 10.000 números do banco.
- **Pronto quando:** `extract_case_number("resuma o 0000007-79.2023.8.99.9014")` devolve o número, e texto sem número devolve `None`.
- **Depende de:** T1.6.

### T2.5 — Índice de busca por palavras em área temporária `[x]`
- **Objetivo:** permitir buscar termos no texto dos documentos e nos nomes das partes, sem alterar o arquivo.
- **Passos:** `create_search_index(connection)` cria as tabelas FTS5 `temp.document_search` (de `documento.texto`) e `temp.party_search` (de `parte.nome`), sem diferença de acentos nem maiúsculas; medir quanto tempo leva. **Medido: 0,35 s (mediana de 5 execuções) para os 25.582 documentos e 14.966 partes.** Função separada de `connect()`, chamada uma vez por sessão (D32).
- **Pronto quando:** uma busca por "ônus da prova" retorna documentos, o teste da T2.3 continua passando e o tempo de criação está anotado.
- **Depende de:** T2.1, T2.3.
