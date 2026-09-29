# E05 — Agente no terminal

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** um chat no terminal (`uv run case-assistant`) em que o modelo usa as ferramentas para responder, funcionando tanto com o modelo local quanto com o modelo em nuvem (Gemini, D30; Claude opcional).
**Por que antes da interface web:** separa o "cérebro" da "tela" e vira o plano B da demonstração se o navegador der problema.

---

### T5.1 — Estado da sessão `[x]`
- **Objetivo:** um objeto `Session` que guarda a conexão com o banco e o processo em foco.
- **Passos:** `dataclass` em `src/case_assistant/session.py` (módulo próprio, sem depender do Pydantic AI) com `connection` e `focused_case_number: str | None`; `open_session()` abre o banco somente leitura, monta o índice de busca uma vez para a conversa inteira (D32) e fecha a conexão ao final.
- **Pronto quando:** a sessão abre com conexão somente leitura, índice pronto e sem foco, e fecha a conexão ao terminar. As ferramentas continuam recebendo a conexão (não a abrem, `AGENTS.md`); o agente passa `session.connection` a elas na T5.4.
- **Depende de:** E03.

### T5.2 — Instruções do agente, versão 1 `[x]`
- **Objetivo:** o texto de instruções fixas (system prompt) em `prompts.py`.
- **Passos:** `SYSTEM_PROMPT` em `prompts.py`: papel ("assistente de consulta a processos do TJSC"), idioma português, 8 regras (só afirmar o que veio de ferramenta; citação `[doc 7878 — Sentença, 18/02/2026]` e `[mov. 9219 — …]`; "Não consta no banco"; repassar os `warnings`; julgamento só pelo campo `judgment`; homônimos; minuta rotulada; datas e valores no formato brasileiro), guia de qual das 9 ferramentas usar e a descrição do banco (T4.5). Testes garantem que toda ferramenta citada existe no código. Medido: 4.348 caracteres, ~1.240 tokens. As regras de limite são testadas contra o modelo e refinadas no E07.
- **Pronto quando:** o texto está revisado e cabe em ~1.500 tokens.
- **Depende de:** T4.5.

### T5.3 — Criar o agente com modelo configurável `[x]`
- **Objetivo:** criar o agente do Pydantic AI lendo o modelo de `LLM_MODEL`.
- **Passos:** `build_agent()` em `agent.py`: `Agent(model de LLM_MODEL, deps_type=Session, system_prompt=SYSTEM_PROMPT)`; sem nenhum `if` por fornecedor; `LLM_MODEL` ausente gera erro claro. Nível de raciocínio pela variável opcional `LLM_THINKING`, repassada à configuração genérica `thinking` do Pydantic AI — resolve o "raciocínio low" do Gemini (D30) sem código por fornecedor; o modelo local deixa vazio (não raciocina). Testes com o `TestModel` do Pydantic AI, sem IA nem rede. `.env.example` ganha `LLM_THINKING` e `PYDANTIC_AI_NO_BANNER=1` (esconde um aviso da biblioteca no terminal). Medido com o modelo local: "olá" respondido em 0,9 s (~1.345 tokens de entrada, quase todos das instruções).
- **Pronto quando:** o agente responde "olá" com o modelo local.
- **Depende de:** T5.1, T5.2.

### T5.4 — Registrar as ferramentas no agente `[x]`
- **Objetivo:** tornar as ferramentas visíveis para o modelo (8 do E03 + `run_sql` do E04).
- **Passos:** `agent_tools.py` com 9 adaptadores que pegam `session.connection` e chamam a ferramenta; docstrings escritas para o modelo (primeira linha = quando usar; `Args` = cada parâmetro), que o Pydantic AI transforma na descrição da ferramenta. Os adaptadores são `async`: o Pydantic AI roda ferramentas síncronas em outras threads, e a conexão SQLite só funciona na thread que a criou — assim elas rodam na thread da conversa, uma de cada vez, sem desligar a proteção do SQLite nem arriscar duas ferramentas usando a conexão (e o autorizador da `run_sql`) ao mesmo tempo. Teste sem IA: o `TestModel` chama as 9 ferramentas com argumentos gerados. Medido com o modelo local: listou as 9; entrada de ~2.900 tokens (as descrições somam ~1.550); 1ª pergunta da sessão 19–27 s, seguintes 1–2 s (o Ollama reaproveita o começo do contexto, que não muda).
- **Pronto quando:** perguntar "quais ferramentas você tem?" lista as 9.
- **Depende de:** T5.3, E04.

### T5.5 — Loop de conversa no terminal `[x]`
- **Objetivo:** `cli.py` que lê a pergunta, responde e guarda o histórico.
- **Passos:** `cli.chat()` — laço `input()` → `agent.run_sync(pergunta, message_history=historico, deps=sessao)`; `sair`, Ctrl+D e Ctrl+C encerram; cada ferramenta chamada aparece como `→ find_case(case_number='…')`; falha do modelo vira mensagem e a conversa continua; entrada e saída injetáveis, para testar com roteiro e `TestModel`; o chat esconde o aviso de observabilidade do Pydantic AI mesmo com `.env` antigo. Medido com o modelo local: "quem é o juiz do processo 0000007-79…?" → `find_case`, resposta certa com o aviso de juiz aposentado; "e qual é o valor da causa?" → R$ 3.796,73 pelo histórico, sem nova ferramenta — mas sem citar a fonte (tratado na T7.7).
- **Pronto quando:** `uv run case-assistant` abre o chat e mantém duas perguntas seguidas.
- **Depende de:** T5.4.

### T5.6 — Primeira pergunta real com o modelo local `[x]`
- **Objetivo:** validar o caminho completo com o modelo local (`qwen3:4b-instruct-2507-q4_K_M`).
- **Passos:** perguntar "quem são as partes do processo 0000007-79.2023.8.99.9014?"; anotar ferramentas chamadas, tempo e qualidade.
- **Pronto quando:** a resposta traz as partes corretas e cita a fonte; o resultado está anotado no `DECISOES.md`.
- **Resultado (D40):** 3 de 3 com a ferramenta certa (`list_parties`) e as partes corretas; 35 s na primeira, 13–14 s nas seguintes. **Não citou a fonte** — as instruções não têm formato para dados do cadastro; levado para a T7.7. Contexto do Ollama em 4.096 tokens (instruções + ferramentas já ocupam ~2.900) — levado para a T11.1.
- **Depende de:** T5.5.

### T5.7 — Mesma pergunta com o modelo em nuvem (Gemini) `[x]`
- **Objetivo:** provar que a troca de modelo é só configuração.
- **Passos:** mudar `LLM_MODEL` para `google:gemini-3.8-flash` no `.env` (D30); repetir a pergunta da T5.6; comparar. Lembrar que no Gemini o limite de saída inclui o raciocínio (T1.9).
- **Pronto quando:** funciona sem mudar nenhuma linha de código; a comparação está anotada.
- **Resultado (D41):** nenhuma linha de código alterada; 3/3 com a ferramenta e as partes corretas, em 6–11 s (local: 35 s na 1ª, 13–14 s depois); citou a fonte em 2/3, em formato próprio; **2 recusas 503** do plano gratuito na 1ª rodada (resposta na 3ª tentativa, ~27 s).
- **Depende de:** T5.6.

### T5.8 — Pergunta 1 do edital: resumo do processo `[x]`
- **Objetivo:** responder "Resuma o processo 0000007-79.2023.8.99.9014, destacando os principais fatos e o andamento processual".
- **Passos:** rodar nos dois modelos; conferir se leu a petição inicial e a sentença e se citou os ids.
- **Pronto quando:** o resumo está correto, cita documentos e o que deu errado (se algo) está anotado.
- **Primeira tentativa (D42):** modelo local chamou só `find_case` nas 3 rodadas — resumo raso, sem ler petição inicial nem sentença, e uma pequena alucinação em 1 de 3; Gemini não testado — cota gratuita de 20 pedidos/dia esgotada. Antes de repetir: roteiro de resumo nas instruções; novas tentativas por pedido e sem repetir cota diária esgotada (ajustes da T5.9); modelo em nuvem com cota suficiente (pendência).
- **Resultado (D43):** com o roteiro de resumo nas instruções, os dois modelos leem inicial, contestação e sentença. Gemini pago: resumo correto, completo (inclui a fase recursal) e citado, em 12–15 s. Local: correto no essencial, mas omite a fase recursal, erra honorários em 1 de 2 e não cita ids, em 128–144 s; exigiu contexto de 8.192 tokens no Ollama.
- **Depende de:** T5.7.

### T5.9 — Repetir automaticamente pedidos recusados pelo serviço do modelo `[x]`
- **Objetivo:** quando o serviço do modelo recusar um pedido por indisponibilidade temporária, tentar de novo sozinho em vez de mostrar a falha na primeira recusa — e **avisar o usuário** de que está tentando de novo e por quê (D41).
- **Passos:** no chat (`cli._ask`), tratar as recusas temporárias — erro 503 ("serviço indisponível / alta demanda"), 429 ("limite de pedidos") e falhas de conexão com o modelo; esperar alguns segundos, com espera crescente, e repetir até 3 vezes; **a cada nova tentativa, mostrar ao usuário uma mensagem como "O serviço do modelo está indisponível no momento (erro 503). Tentando de novo em 5 s… (tentativa 2 de 3)"**, para a espera nunca parecer travamento; só depois da última tentativa mostrar a falha. Erros que não são temporários (chave inválida, pedido malformado) não são repetidos. Vale para qualquer provedor, sem `if` por fornecedor.
- **Pronto quando:** testes sem IA simulam uma recusa 503 seguida de sucesso (resposta chega, com o aviso de nova tentativa exibido), três recusas seguidas (aviso a cada tentativa e falha final) e um erro não temporário (falha imediata, sem repetir).
- **Implementado:** `run_with_retries` em `agent.py` (reaproveitável pela interface web do E10), usado por `cli._ask`; temporários = HTTP 429, 500, 502, 503, 504 e falha de conexão (`ModelAPIError` sem código, ex.: Ollama fechado); esperas de 5 s e 10 s; aviso ao usuário a cada nova tentativa; erros como 400/401/403/404 falham na hora.
- **Depende de:** T5.5.
