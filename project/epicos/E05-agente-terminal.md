# E05 — Agente no terminal

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** um chat no terminal (`uv run case-assistant`) em que o modelo usa as ferramentas para responder, funcionando tanto com o modelo local quanto com o Claude.
**Por que antes da interface web:** separa o "cérebro" da "tela" e vira o plano B da demonstração se o navegador der problema.

---

### T5.1 — Estado da sessão `[ ]`
- **Objetivo:** um objeto `Sessao` que guarda a conexão com o banco e o `processo_em_foco`.
- **Passos:** `dataclass` em `agent.py` com `conexao` e `processo_em_foco: str | None`.
- **Pronto quando:** as ferramentas recebem a sessão como parâmetro.
- **Depende de:** E03.
- **Para explicar à banca:** "A sessão é a memória de trabalho do agente: sabe com qual banco fala e de qual processo estamos tratando."

### T5.2 — Instruções do agente, versão 1 `[ ]`
- **Objetivo:** o texto de instruções fixas (system prompt) em `prompts.py`.
- **Passos:** papel ("assistente de consulta a processos do TJSC"), idioma português, "só afirme o que veio de uma ferramenta", formato de citação `[doc 7878 — Sentença, 18/02/2026]`, descrição do banco (T4.5).
- **Pronto quando:** o texto está revisado e cabe em ~1.500 tokens.
- **Depende de:** T4.5.
- **Para explicar à banca:** "As regras de comportamento estão num único arquivo, legível por qualquer pessoa."

### T5.3 — Criar o agente com modelo configurável `[ ]`
- **Objetivo:** criar o agente do Pydantic AI lendo o modelo de `LLM_MODEL`.
- **Passos:** carregar `.env`; `Agent(model=os.environ["LLM_MODEL"], deps_type=Sessao, system_prompt=...)`; sem nenhum `if` por fornecedor.
- **Pronto quando:** o agente responde "olá" com o modelo local.
- **Depende de:** T5.1, T5.2.
- **Para explicar à banca:** "O mesmo código fala com o modelo local ou com o Claude; não existe caminho especial para nenhum."

### T5.4 — Registrar as ferramentas no agente `[ ]`
- **Objetivo:** tornar as 7 ferramentas visíveis para o modelo.
- **Passos:** registrar cada função com `@agent.tool`; revisar a descrição (docstring) de cada uma, que é o que o modelo lê para decidir.
- **Pronto quando:** perguntar "quais ferramentas você tem?" lista as 7.
- **Depende de:** T5.3, E04.
- **Para explicar à banca:** "O modelo decide pela descrição de cada ferramenta — por isso elas são curtas e específicas."

### T5.5 — Loop de conversa no terminal `[ ]`
- **Objetivo:** `cli.py` que lê a pergunta, responde e guarda o histórico.
- **Passos:** laço `input()` → `agent.run_sync(pergunta, message_history=historico, deps=sessao)`; comando `sair`; imprimir cada ferramenta chamada.
- **Pronto quando:** `uv run case-assistant` abre o chat e mantém duas perguntas seguidas.
- **Depende de:** T5.4.
- **Para explicar à banca:** "O terminal mostra cada consulta que o agente faz — dá para ver ele decidindo."

### T5.6 — Primeira pergunta real com o modelo local `[ ]`
- **Objetivo:** validar o caminho completo com o modelo local (`qwen3:4b-instruct-2507-q4_K_M`).
- **Passos:** perguntar "quem são as partes do processo 0000007-79.2023.8.99.9014?"; anotar ferramentas chamadas, tempo e qualidade.
- **Pronto quando:** a resposta traz as partes corretas e cita a fonte; o resultado está anotado no `DECISOES.md`.
- **Depende de:** T5.5.
- **Para explicar à banca:** "O primeiro teste de ponta a ponta foi com o modelo local, porque é o cenário mais difícil."

### T5.7 — Mesma pergunta com o Claude `[ ]`
- **Objetivo:** provar que a troca de modelo é só configuração.
- **Passos:** mudar `LLM_MODEL` no `.env`; repetir a pergunta da T5.6; comparar.
- **Pronto quando:** funciona sem mudar nenhuma linha de código; a comparação está anotada.
- **Depende de:** T5.6.
- **Para explicar à banca:** "Troquei o modelo mudando uma linha de configuração, ao vivo."

### T5.8 — Pergunta 1 do edital: resumo do processo `[ ]`
- **Objetivo:** responder "Resuma o processo 0000007-79.2023.8.99.9014, destacando os principais fatos e o andamento processual".
- **Passos:** rodar nos dois modelos; conferir se leu a petição inicial e a sentença e se citou os ids.
- **Pronto quando:** o resumo está correto, cita documentos e o que deu errado (se algo) está anotado.
- **Depende de:** T5.7.
- **Para explicar à banca:** "O resumo segue o caminho: dados básicos → índice dos documentos → leitura só dos relevantes → texto com citações."
