# E06 — Memória da conversa

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** depois de perguntar sobre um processo, o usuário pode continuar com "e quem é o juiz?" sem repetir o número.
**Por que importa:** é o requisito "Conversar" do edital. Modelos pequenos se perdem em conversas longas, então o processo atual fica guardado num campo explícito, não só no histórico.

---

### T6.1 — Guardar o processo em foco `[x]`
- **Objetivo:** as ferramentas que recebem um número de processo gravam o número encontrado em `session.focused_case_number`.
- **Passos:** nos adaptadores de `agent_tools.py`, `find_case`, `list_parties`, `list_movements` e `list_documents` atualizam o foco sempre que o processo é encontrado (não só `find_case`: na T5.6 o modelo foi direto a `list_parties`); processo não encontrado não muda o foco; buscas que devolvem vários processos (`search_cases`, `search_parties`, `search_text`) também não. As ferramentas de `tools.py` continuam sem conhecer a sessão.
- **Pronto quando:** teste sem IA: após `find_case("0000007-...")`, a sessão contém esse número — e o mesmo para as outras três ferramentas.
- **Depende de:** T5.1.
- **Para explicar à banca:** "O processo em discussão fica anotado num campo, como um marcador de página."

### T6.2 — Lembrar o modelo a cada pergunta `[x]`
- **Objetivo:** incluir "Processo em foco: X" nas instruções a cada turno.
- **Passos:** usar instruções dinâmicas do Pydantic AI com acesso à sessão. Foi usado `instructions`, e não `@agent.system_prompt`, porque só as instruções são recalculadas a cada pedido e ficam fora do histórico (D44).
- **Pronto quando:** após perguntar sobre o 3161, a pergunta "qual o valor da causa?" é respondida sobre o 3161.
- **Depende de:** T6.1.
- **Para explicar à banca:** "Em vez de esperar que o modelo lembre, eu lembro por ele a cada pergunta."

### T6.3 — Ferramentas usam o foco quando falta o número `[ ]`
- **Objetivo:** chamar `listar_partes()` sem número usa o processo em foco.
- **Passos:** parâmetro `numero` opcional em todas as ferramentas de processo; sem número e sem foco → aviso "informe o número do processo".
- **Pronto quando:** testes sem IA cobrem os três casos (com número, com foco, sem nenhum).
- **Depende de:** T6.1.
- **Para explicar à banca:** "Se o modelo esquecer de passar o número, a ferramenta completa sozinha."

### T6.4 — Trocar de processo no meio da conversa `[ ]`
- **Objetivo:** ao citar um novo número, o foco muda e as perguntas seguintes vão para ele.
- **Passos:** roteiro manual: 3161 → pergunta → processo 1 → "e as partes?"; verificar a resposta.
- **Pronto quando:** as respostas seguem o processo correto; roteiro salvo para a bateria de avaliação (E09).
- **Depende de:** T6.2, T6.3.
- **Para explicar à banca:** "Testei a troca de assunto porque é onde agentes de conversa costumam misturar informações."
