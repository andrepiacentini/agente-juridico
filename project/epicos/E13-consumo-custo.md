# E13 — Consumo e custo

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** cada resposta mostra quanto consumiu (tokens, custo e tempo), e um painel dentro do chat mostra o acumulado histórico, por sessão e por modelo, com a projeção de custo para o uso real do tribunal.
**Por que incluir:** o custo é uma das perguntas centrais do desafio (mais perguntas, mais usuários, base maior). Com números medidos, dá para comparar o modelo pago (mais rápido e melhor, com custo por uso) com um modelo próprio (custo fixo, dados sem sair do tribunal), em vez de opinar. Decisão: D71.

**Regras que atravessam o épico:**
- O registro de uso fica num arquivo próprio (SQLite separado, caminho no `.env`); o `desafio.sqlite` continua somente leitura.
- Preço por modelo e câmbio vêm da configuração, com a data da cotação; nada fixo no código. Modelo local custa zero por token.

---

### T13.1 — Registrar o uso de cada resposta `[x]`
- **Objetivo:** gravar, a cada resposta, sessão, modelo, tokens de entrada e de saída, ferramentas chamadas, tempo e data.
- **Passos:** ler os tokens de `result.usage` do Pydantic AI; gravar num SQLite próprio, no caminho de uma variável do `.env`; registrar no chat web, no terminal e na bateria (a bateria também passa a gravar os tokens no JSON de respostas). Testes sem IA.
- **Pronto quando:** uma pergunta no chat, no terminal e na bateria gera o registro, e os testes confirmam que o `desafio.sqlite` não é tocado.
- **Depende de:** E10.

### T13.2 — Tabela de preços por modelo `[x]`
- **Objetivo:** calcular o custo de cada resposta a partir dos tokens.
- **Passos:** preço por milhão de tokens (entrada e saída) de cada modelo e câmbio dólar–real em configuração, com a data da cotação e a fonte (página oficial de preços); modelo local com preço zero; função de custo testada.
- **Pronto quando:** o custo de uma resposta de exemplo bate com a conta feita à mão.
- **Depende de:** T13.1.

### T13.3 — Consumo em cada resposta `[x]`
- **Objetivo:** mostrar, abaixo de cada resposta do chat web, tokens, custo e tempo ("3.214 tokens · R$ 0,004 · 11 s"), e o acumulado da sessão.
- **Passos:** rodapé discreto na mensagem; total da sessão acumulado junto com o histórico.
- **Pronto quando:** uma pergunta no navegador mostra o rodapé com os números do registro.
- **Depende de:** T13.2, E10.

### T13.4 — Painel de consumo dentro do chat `[x]`
- **Objetivo:** um botão "Ver consumo" no chat que mostra tabelas e gráficos do acumulado histórico, por sessão, por modelo e por tipo de pergunta.
- **Passos:** ação do Chainlit que monta o painel na conversa; gráficos com o Plotly (elemento suportado pelo Chainlit; dependência nova); tabelas com os totais; tudo lido do registro da T13.1.
- **Pronto quando:** depois de algumas perguntas nos dois modelos, o painel mostra os números certos e os gráficos na própria conversa.
- **Depende de:** T13.3.

### T13.5 — Projeção de custo e ponto de equilíbrio `[x]`
- **Objetivo:** com o consumo medido, projetar o custo mensal para o uso real (usuários × perguntas por dia × mix de tipos) e comparar com um servidor próprio com modelo aberto.
- **Passos:** rodar a bateria (E09) uma vez em cada modelo com o registro ligado; custo médio por tipo de pergunta; projeção em cenários de uso; custo do servidor próprio como estimativa declarada, com fonte; ponto de equilíbrio; mostrar a projeção no painel; registrar no `DECISOES.md`.
- **Pronto quando:** a tabela de cenários e o ponto de equilíbrio estão no `DECISOES.md` e no painel.
- **Depende de:** T13.4.
