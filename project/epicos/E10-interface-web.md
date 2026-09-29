# E10 — Interface web

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** chat no navegador (Chainlit) em que cada consulta do agente aparece como um passo que pode ser aberto para ver o que foi consultado.
**Por que importa:** torna visível o requisito "Fundamentar" — a banca vê o agente decidir. Se faltar tempo, a demo fica no terminal (E05).

---

### T10.1 — Chat mínimo no navegador `[x]`
- **Objetivo:** `app.py` que conversa usando o mesmo agente do terminal.
- **Passos:** criar sessão ao abrir o chat; guardar histórico por usuário; chamar o agente a cada mensagem.
- **Pronto quando:** `uv run chainlit run app.py` abre o chat e responde a duas perguntas seguidas.
- **Depende de:** E06.
- **Para explicar à banca:** "A interface é uma camada fina; toda a lógica está no agente, que é o mesmo do terminal."

### T10.2 — Mostrar cada consulta como passo `[x]`
- **Objetivo:** exibir nome da ferramenta, parâmetros e resultado de cada chamada.
- **Passos:** transformar cada chamada de ferramenta em um `cl.Step` recolhível.
- **Pronto quando:** a pergunta de resumo do 3161 mostra os passos na ordem.
- **Depende de:** T10.1.
- **Para explicar à banca:** "Dá para abrir cada passo e conferir exatamente o que o agente leu antes de responder."

### T10.3 — Escolha do modelo na tela `[ ]`
- **Objetivo:** trocar entre modelo local e Claude sem reiniciar.
- **Passos:** usar as configurações de chat do Chainlit; criar o agente com o modelo escolhido.
- **Pronto quando:** a troca funciona no meio da demonstração.
- **Depende de:** T10.1.
- **Para explicar à banca:** "Na demo mostro a mesma pergunta nos dois modelos, lado a lado."

### T10.4 — Tela de boas-vindas com exemplos `[ ]`
- **Objetivo:** mensagem inicial com as 4 perguntas do edital prontas para clicar.
- **Passos:** mensagem de abertura com botões de exemplo usando o processo 3161.
- **Pronto quando:** clicar num exemplo envia a pergunta.
- **Depende de:** T10.1.
- **Para explicar à banca:** "Quem nunca viu o sistema sabe por onde começar."
