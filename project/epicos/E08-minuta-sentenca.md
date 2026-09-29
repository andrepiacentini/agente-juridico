# E08 — Minuta de sentença

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** o agente redige uma proposta de sentença baseada nos documentos do processo, sempre identificada como proposta, ou recusa com explicação quando faltam peças.
**Por que é separado:** é a pergunta 4 do edital e a de maior risco — um texto que parece sentença proferida é inaceitável.

---

### T8.1 — Verificar se há base para a minuta `[x]`
- **Objetivo:** função que diz se o processo tem petição inicial **e** contestação.
- **Passos:** consulta nos tipos de documento; devolver "apto" ou "faltam: <lista>".
- **Pronto quando:** teste sem IA: 3161 → apto; processo 1 → faltam ambas.
- **Depende de:** T3.7.

### T8.2 — Estrutura da minuta `[x]`
- **Objetivo:** modelo de texto com Relatório, Fundamentação e Dispositivo, e as regras de redação.
- **Passos:** escrever em `prompts.py`: usar só os documentos lidos, citar ids, não inventar jurisprudência.
- **Pronto quando:** o modelo de texto está revisado.
- **Depende de:** T5.2.

### T8.3 — Aviso obrigatório no topo `[x]`
- **Objetivo:** garantir, por código, que toda minuta comece com "PROPOSTA DE MINUTA — texto não proferido".
- **Passos:** ao detectar uma minuta na resposta, inserir o aviso se o modelo não tiver colocado; teste sem IA para a função.
- **Pronto quando:** o teste passa com e sem o aviso vindo do modelo.
- **Depende de:** T8.2.

### T8.4 — Recusa explicada `[x]`
- **Objetivo:** "elabore uma minuta para o processo 1" é recusado com o motivo.
- **Passos:** regra nas instruções usando a T8.1; testar com o processo 1.
- **Pronto quando:** a resposta explica quais peças faltam e não produz texto de sentença.
- **Depende de:** T8.1, E05.

### T8.5 — Minuta do processo 3161 `[x]`
- **Objetivo:** gerar a minuta completa do 3161 nos dois modelos.
- **Passos:** rodar; conferir aviso, estrutura, citações e ausência de fatos inventados; anotar tempo e qualidade.
- **Pronto quando:** a minuta está aceitável em pelo menos um modelo e a comparação está no `DECISOES.md`.
- **Depende de:** T8.1 a T8.3.
