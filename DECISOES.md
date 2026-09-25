# Registro de decisões

Linha do tempo das decisões do projeto, separadas por dia. Cada decisão traz **o que foi decidido**, **por quê** e, quando houve, **o que foi descartado**. O registro é feito no momento em que a decisão acontece — não reconstruído no final.

Termos técnicos têm link para o [glossário](docs/glossario.md). Detalhes técnicos completos estão no [`plan.md`](docs/plan.md); o planejamento das tarefas está no [roadmap](project/ROADMAP.md).

Também ficam registrados aqui os pontos em que o assistente de IA usado no desenvolvimento (Claude Code) ajudou, errou ou precisou ser corrigido — é tema da pergunta 3 da arguição.

---

## 22/09/2026

### D01 — Estudar o banco antes de escolher a arquitetura
- **Decisão:** antes de escrever qualquer código, analisar o conteúdo do `desafio.sqlite`: tabelas, volumes, campos vazios e contradições.
- **Por quê:** a escolha da arquitetura depende do formato dos dados. A análise revelou que o banco tem armadilhas plantadas (ver D13), que definiram boa parte do projeto.
- **Uso de IA:** o Claude Code executou as consultas de análise e resumiu os números; os resultados estão no `plan.md` §2.

### D02 — Agente que consulta o banco, e não RAG
- **Decisão:** construir um [agente](docs/glossario.md#agente) que consulta o banco por meio de [ferramentas](docs/glossario.md#ferramenta), em vez de usar [RAG](docs/glossario.md#rag) com [banco vetorial](docs/glossario.md#banco-vetorial).
- **Por quê:**
  - As perguntas do desafio partem sempre de um **número de processo** — uma código exato. Busca por "significado parecido" ([embeddings](docs/glossario.md#embedding)) é ruim justamente com códigos exatos.
  - Partes, magistrado, datas e valores estão em **colunas** do banco, não em texto corrido. Isso dificulta a composição de uma RAG para uso por uma LLM.
  - Um processo inteiro cabe na memória de trabalho do modelo ([contexto](docs/glossario.md#contexto)); não é preciso [fatiar documentos (chunking)](docs/glossario.md#chunking) — o que ainda poderia cortar uma sentença no meio.
  - Quando uma consulta ao banco volta vazia, a resposta honesta é "não consta". O RAG sempre devolve *algum* trecho, mesmo sem relação — o que favorece [alucinação](docs/glossario.md#alucinacao).
  - Menos programas rodando ao mesmo tempo num computador de 8 GB, que foi o equipamento base usado para desenvolver o código deste desafio.
- **Descartado:** RAG com Qdrant e embeddings (a ideia inicial que pensei para o projeto, por usar um contéudo de dados externo a LLM). Se no futuro for preciso buscar "processos parecidos com este", o caminho é o [sqlite-vec](docs/glossario.md#sqlite-vec), sem servidor extra.

### D03 — Ferramentas prontas como caminho principal; SQL livre só como válvula de escape
- **Decisão:** a maior parte das perguntas é respondida por 6 ferramentas com consultas escritas à mão. Uma sétima ferramenta permite ao modelo escrever [SQL](docs/glossario.md#sql) próprio, só para perguntas imprevistas.
- **Por quê:** modelos pequenos, como o que está sendo usado (`qwen3:4b`) erram ao escrever SQL do zero ([Text-to-SQL](docs/glossario.md#text-to-sql)): inventam colunas e esquecem as regras do banco. Escolher *qual* ferramenta usar é uma decisão bem mais fácil para eles. A opção de termos um SQL livre foi devido ao desafio avisar que as perguntas de exemplo "não esgotam as perguntas que poderão ser feitas".
- **Descartado:** Text-to-SQL livre como abordagem única, pelo risco de um modelo de LLM pequeno, que irá ser executado localmente, alucinar.

### D04 — Banco aberto em modo somente leitura
- **Decisão:** o banco é sempre aberto em modo [somente leitura](docs/glossario.md#somente-leitura). Índices de busca são criados em [tabelas temporárias](docs/glossario.md#tabela-temporaria), nunca no arquivo original, evitando quebra de integridade dos dados da fonte.
- **Por quê:** o agente vai gerar consultas sozinho. A garantia de que nada é alterado precisa vir do próprio banco, e não da obediência do modelo. O arquivo original também precisa continuar idêntico ao entregue pela banca.

### D05 — Primeiro os metadados, o texto só quando necessário
- **Decisão:** as ferramentas de listagem devolvem apenas [metadados](docs/glossario.md#metadados) (id, tipo, data, autor). O texto de um documento só é lido quando o agente pede aquele documento específico.
- **Por quê:** um processo pode ter 19 documentos. Entregar todos de uma vez deixaria o modelo lento e poderia estourar a memória do computador. Assim, o modelo vê o "índice" e escolhe o que ler — como uma pessoa faria.

### D06 — Pydantic AI como biblioteca do agente
- **Decisão:** usar o [Pydantic AI](docs/glossario.md#pydantic-ai) para o laço do agente.
- **Por quê:** transforma funções Python comuns em ferramentas, funciona igual com modelo local e de nuvem, mantém o histórico da conversa e tem pouca "mágica" escondida — o código fica pequeno e fácil de explicar.
- **Descartado:** [LangChain e LlamaIndex](docs/glossario.md#langchain) (camadas demais, centrados em RAG); bibliotecas de múltiplos agentes, como CrewAI (complexidade desnecessária para um agente só); escrever o laço à mão (daria para fazer, mas reimplementaria o que a biblioteca já resolve).

### D07 — Python 3.12, gerenciado pelo uv
- **Decisão:** [Python](docs/glossario.md#python) com [uv](docs/glossario.md#uv), com a versão 3.12 fixada.
- **Por quê:** o Python já traz o [SQLite](docs/glossario.md#sqlite) embutido e tem o ecossistema de IA mais maduro. O [uv](docs/glossario.md#uv) garante a mesma instalação em qualquer máquina, inclusive na da banca.
- **Descartado:** TypeScript (ecossistema de agentes locais menos maduro).

### D08 — Modelo local Qwen3 4B, com Claude como alternativa em nuvem
- **Decisão:** usar o [modelo local](docs/glossario.md#modelo-local) `qwen3:4b` via [Ollama](docs/glossario.md#ollama) como padrão e o Claude (Anthropic) em nuvem como alternativa. A troca é feita por uma [variável de ambiente](docs/glossario.md#variavel-de-ambiente), sem mudar o código.
- **Por quê:** o máquina hospedeira do projeto tem 8 GB de [RAM](docs/glossario.md#ram). O Qwen3 4B [comprimido](docs/glossario.md#quantizacao) ocupa ~2,6 GB, é o melhor da sua faixa em uso de ferramentas e responde bem em português. Ter o Claude como alternativa mostra que a solução não depende de um fornecedor e protege a demonstração caso o modelo local falhe ao vivo. Rodar localmente também demonstra um caminho para dados sigilosos (nada sai da máquina).
- **Descartado:** Llama 3.1 8B (grande demais para a memória disponível), Gemma 3 4B (não suporta ferramentas no Ollama), Llama 3.2 3B (fraco no uso de ferramentas).

### D09 — Chainlit como interface web
- **Decisão:** usar o [Chainlit](docs/glossario.md#chainlit) para o chat no navegador.
- **Por quê:** além da conversa, mostra cada consulta que o agente fez como um passo que pode ser aberto. Isso torna visível o requisito "Fundamentar" do edital: a banca vê o que foi consultado antes de cada resposta.
- **Descartado:** Streamlit e Gradio (mostrar os passos exigiria código extra); interface própria em React (custo alto, sem ganho para o desafio).

### D10 — Terminal antes da interface web
- **Decisão:** o agente funciona primeiro no [terminal](docs/glossario.md#cli); a interface web vem depois.
- **Por quê:** obriga a separar a lógica do agente da tela, e o terminal serve de plano B na demonstração se o navegador der problema.

### D11 — "Processo em foco" guardado explicitamente
- **Decisão:** o processo em discussão fica guardado num campo da sessão e é lembrado ao modelo a cada pergunta.
- **Por quê:** o edital exige manter o contexto entre perguntas ([multi-turno](docs/glossario.md#multi-turno)). Modelos pequenos se perdem em conversas longas; um campo explícito é mais barato e mais confiável do que esperar que o modelo releia todo o histórico.

### D12 — "Já foi julgado?" é respondido cruzando três sinais
- **Decisão:** a situação de julgamento é calculada pelo código, cruzando a data de sentença, as [movimentações](docs/glossario.md#movimentacao) de sentença e a existência do documento de Sentença.
- **Por quê:** os sinais se contradizem com frequência — na analise dos dados do sqlite fornecido, existem 4.426 processos com data de sentença mas sem o documento, e 37 no sentido contrário. Entregar o resultado já cruzado evita que o modelo tire conclusões a partir de uma variável só.

### D13 — Inconsistências do banco são reportadas, nunca corrigidas
- **Decisão:** quando o cadastro está incompleto ou contraditório (magistrado ausente, juiz aposentado, comarca divergente, valor da causa vazio, homônimos), o agente informa o problema e não escolhe uma versão.
- **Por quê:** o banco foi construído para testar o requisito "Reconhecer limites" — 63% dos processos não têm nenhum documento. Num contexto judicial, esconder uma divergência é pior do que mostrá-la. No caso dos homônimos, o agente pergunta de qual pessoa se trata.

### D14 — Minuta de sentença sempre rotulada, e recusada sem base
- **Decisão:** toda [minuta](docs/glossario.md#minuta) começa com "PROPOSTA DE MINUTA — texto não proferido" (garantido pelo código, não só pelas instruções). Se o processo não tiver petição inicial e contestação, a minuta é recusada com explicação.
- **Por quê:** o edital exige que a minuta não seja apresentada como sentença proferida. Sem o pedido do autor e a defesa do réu, qualquer minuta seria inventada.

### D15 — Incluir testes, mesmo sendo opcionais
- **Decisão:** [testes automatizados](docs/glossario.md#teste-automatizado) das ferramentas (sem IA) e uma [bateria de perguntas de avaliação](docs/glossario.md#golden-set).
- **Por quê:** as ferramentas sempre dão o mesmo resultado, então podem ser testadas de forma barata e cobrem as armadilhas do banco. A bateria de perguntas avisa quando uma mudança nas instruções do agente conserta uma resposta e estraga outra. Cobertura de testes e pipeline de integração contínua ficaram de fora: custo sem retorno para o desafio.

### D16 — Busca por palavras com o recurso nativo do SQLite
- **Decisão:** para buscar termos nos documentos e nomes de partes, usar o [FTS5](docs/glossario.md#fts5), que já vem no SQLite.
- **Por quê:** cobre perguntas como "em quais processos aparece 'inversão do ônus da prova'?" sem nenhum programa ou servidor adicional.

### D17 — Planejamento em tarefas pequenas e explicáveis
- **Decisão:** dividir o trabalho em 12 épicos e 72 tarefas curtas, cada uma com objetivo, passos, critério de conclusão e uma frase para a apresentação ([roadmap](project/ROADMAP.md)).
- **Por quê:** cada tarefa precisa ter começo, meio e fim claros e poder ser explicada aos stakeholders sem depender de outras. Tarefas grandes misturam temas e escondem decisões.
- **Uso de IA:** o Claude Code gerou a primeira versão do roadmap a partir do `plan.md`; ela foi revisada e ajustada pelo autor.

### D18 — Este registro em linguagem simples, com glossário
- **Decisão:** escrever o `DECISOES.md` evitando jargão e explicar os termos técnicos inevitáveis num [glossário](docs/glossario.md) separado.
- **Por quê:** o registro é lido por stakeholders com perfis variados; cada decisão deve ser compreensível sem conhecimento prévio de IA ou tecnologias especializadas.

## 23/09/2026

### D19 — Nomes do código em inglês; textos em português
- **Decisão:** tudo o que é estrutura do código (classes, funções, variáveis, constantes, nomes das ferramentas, tabelas e colunas que o projeto criar) é nomeado em inglês. Comentários, instruções do agente, mensagens e respostas continuam em português. Cada termo jurídico tem uma tradução fixa (processo → `case`, movimentação → `movement`, minuta → `draft` etc.).
- **Por quê:** é o padrão da indústria, facilita a leitura por qualquer desenvolvedor e evita misturar idiomas no mesmo nome. A tradução fixa impede que o mesmo conceito apareça com dois nomes diferentes.
- **Exceção:** as tabelas e colunas do `desafio.sqlite` já vêm em português e o banco é [somente leitura](docs/glossario.md#somente-leitura); elas mantêm o nome original dentro do [SQL](docs/glossario.md#sql) e são traduzidas na entrada do programa.
- **Descartado:** traduzir "parte" como `part`: em inglês jurídico a parte do processo é *party*; `part` significa "pedaço" e daria a entender seções do processo.
- **Uso de IA:** o autor propôs `part`; o Claude Code apontou o sentido jurídico de *party* e o autor manteve `party`.

### D20 — Boas práticas: Clean Code e princípios de arquitetura, na medida do projeto
- **Decisão:** o código segue o [Clean Code](docs/glossario.md#clean-code) de Robert C. Martin e os princípios [SOLID](docs/glossario.md#solid), [KISS, YAGNI e DRY](docs/glossario.md#kiss-yagni-dry), [arquitetura em camadas](docs/glossario.md#arquitetura-em-camadas), [DDD](docs/glossario.md#ddd) leve, [TDD](docs/glossario.md#tdd), [logs estruturados](docs/glossario.md#observabilidade) e os [12 fatores](docs/glossario.md#doze-fatores). As regras estão no `CLAUDE.md`, seção "Padrão de codificação".
- **Por quê:** código legível e organizado é mais fácil de explicar e de alterar sem quebrar. Quando dois princípios entram em conflito, vale o mais simples (KISS/YAGNI): o projeto é pequeno e roda num notebook de 8 GB.
- **Descartado:** microsserviços (um programa só basta) e meta de percentual de cobertura de testes (mantida a decisão D15).

### D21 — Instruções do assistente num arquivo só: `AGENTS.md`
- **Decisão:** as instruções para assistentes de IA ficam todas no `AGENTS.md`. O `CLAUDE.md` tem apenas uma linha que importa o `AGENTS.md` ([CLAUDE.md e AGENTS.md](docs/glossario.md#claude-md)).
- **Por quê:** o `CLAUDE.md` é lido automaticamente só pelo Claude Code; o `AGENTS.md` é o padrão aberto lido por outras ferramentas de IA (Codex, Cursor, Copilot). Com um arquivo só, qualquer ferramenta recebe as mesmas regras e não há duas cópias que possam ficar diferentes com o tempo ([DRY](docs/glossario.md#kiss-yagni-dry)). O `AGENTS.md` foi escolhido como fonte por ser o padrão aberto.
- **Descartado:** manter os dois arquivos com o mesmo conteúdo copiado — foi a primeira versão desta decisão, revista no mesmo dia porque exigia lembrar de alterar os dois juntos.
- **Uso de IA:** o Claude Code sugeriu desde o início um arquivo só apontando para o outro; o autor começou com a cópia e depois adotou a sugestão.

### D22 — Testar a memória com o cenário real da apresentação: Safari + Google Meet
- **Decisão:** o Chainlit será sempre aberto no Safari, só com a aba do chat. Na tarefa T11.6, a demonstração completa será ensaiada com uma chamada do Google Meet aberta em outro navegador, medindo a [pressão de memória](docs/glossario.md#pressao-de-memoria) no Monitor de Atividade. O resultado decide qual modelo vai para a apresentação: o local de 4B, o local de 1.7B ou o da nuvem.
- **Por quê:** o Chainlit precisa de um navegador, e a conta de memória inicial (~7 GB de 8 GB de [RAM](docs/glossario.md#ram)) não incluía a videochamada de uma apresentação remota. Quando a memória acaba, o macOS passa a usar o disco no lugar dela e as respostas do [modelo local](docs/glossario.md#modelo-local) ficam muito mais lentas ([latência](docs/glossario.md#latencia)) — justamente diante da banca. O Safari costuma gastar menos memória que o Chrome no Mac.
- **Descartado:** confiar apenas na estimativa do `plan.md`; e a instrução anterior "fechar o Chrome na demo", que era ambígua, porque um navegador continua sendo necessário.
- **Uso de IA:** o autor percebeu a contradição entre "fechar o Chrome" e usar uma interface web; o Claude Code acrescentou o custo da videochamada, que não estava na conta.

### D23 — Pacote de código `src/case_assistant/`
- **Decisão:** o código do agente fica no pacote `src/case_assistant/` ("assistente de processos").
- **Por quê:** segue a regra de nomes em inglês (D19) e descreve o que o programa faz, sem prender o nome ao tribunal nem à tecnologia.
- **Junto:** o chat no terminal passa a abrir com `uv run case-assistant` (antes `uv run agente`), com o mesmo nome do pacote.
- **Descartado:** `src/agente/` (nome em português, das primeiras versões do plano) e `src/tjsc_agent/` (sugestão do Claude Code; o autor preferiu um nome ligado ao domínio).

## 24/09/2026

### D24 — Uma branch por épico e uma por tarefa
- **Decisão:** cada épico ganha uma [branch](docs/glossario.md#branch) própria, criada a partir da `main` quando a primeira tarefa dele começa. Cada tarefa ganha uma branch nova criada a partir da branch do épico. Os nomes são em inglês e começam por um prefixo que indica o objetivo (`epic/`, `feat/`, `enh/`, `fix/`, `hotfix/`, `docs/` etc.), como `epic/e03-query-tools` e `feat/t3.2-list-parties`. A tarefa pronta volta para o épico, e o épico pronto volta para a `main`, por [pull request](docs/glossario.md#pull-request). A regra está no `AGENTS.md`, seção "Fluxo de branches".
- **Por quê:** a `main` só recebe épicos inteiros e revisados, então está sempre em estado de demonstração. Cada tarefa fica isolada e pode ser mostrada, revisada ou desfeita sem afetar as outras — o que também deixa o histórico do Git alinhado ao [roadmap](project/ROADMAP.md) para a banca.
- **Limpeza:** depois do merge, e só com os checks automáticos aprovados, a branch é apagada — no computador e no GitHub —, para a lista de branches mostrar apenas trabalho em andamento. A branch do épico fica até o épico inteiro entrar na `main`.
- **Descartado:** trabalhar direto na `main` (uma tarefa quebrada estragaria a versão de demonstração) e uma branch só por épico, sem branches de tarefa (misturaria tarefas no mesmo histórico).

## 25/09/2026

### D25 — Modelo local padrão: `qwen3:4b-instruct-2507`, sem modo raciocínio
- **Decisão:** o [modelo local](docs/glossario.md#modelo-local) padrão passa a ser `qwen3:4b-instruct-2507-q4_K_M`, a variante do Qwen3 4B que responde direto, sem [modo raciocínio](docs/glossario.md#thinking). Mesmo tamanho (2,5 GB) e mesma família da D08. A tarefa T11.2 ("desligar o modo raciocínio") foi cancelada: não há o que desligar.
- **Por quê:** no teste da T1.2, com a mesma pergunta ("o que é uma petição inicial?", em até 5 frases) e o mesmo computador:

  | Modelo | Resposta | Tempo total |
  |---|---|---|
  | `qwen3:4b` | raciocinou em inglês, mesmo com o raciocínio pedido como desligado, e esgotou o limite de 400 [tokens](docs/glossario.md#token) sem responder | 23,5 s, sem resposta |
  | `qwen3:4b-instruct-2507` | 5 frases em português, direto | 10,2 s |

  A etiqueta `qwen3:4b` do Ollama hoje aponta para uma versão mais nova do modelo que **só** funciona raciocinando; a opção de desligar é ignorada. O plano (D08) contava com poder desligar.
- **Descartado:** manter `qwen3:4b` — cada resposta gastaria centenas de tokens pensando em inglês antes de começar, o que estoura o limite de 30 s por resposta.
- **Achado de memória:** no primeiro teste, com aplicativos pesados abertos (~5,6 GB juntos), a máquina estava com 4,9 GB em [swap](docs/glossario.md#pressao-de-memoria) e o modelo gerava só 2,2 tokens por segundo. Com esses aplicativos fechados: 19,7 tokens por segundo — 9 vezes mais rápido. Confirma a regra da D22: na demonstração, só o necessário aberto.
- **Uso de IA:** o plano escrito com o Claude Code assumiu que o `think=False` funcionaria no `qwen3:4b`, sem verificar a versão atual do modelo; o erro só apareceu no teste real. O Claude Code identificou a causa (contexto de 262 mil tokens no `ollama show`, típico da versão nova) e propôs a variante *instruct*.

### D26 — Modelo reserva testado já no setup; avaliação de qualidade fica para depois
- **Decisão:** a antiga T11.5 foi dividida. O download e o teste de velocidade e memória do `qwen3:1.7b` viraram a T1.8, no épico de preparação (E01), já concluída. A comparação de qualidade continua na T11.5, depois da bateria de avaliação (E09). Foi criada a T1.9, também no E01, para medir o Claude em nuvem com a mesma pergunta e completar o comparativo dos três modelos no `plan.md` §5.
- **Por quê:** baixar e medir velocidade é preparação de ambiente e não depende de nada; saber se o modelo menor escolhe a ferramenta certa e não inventa dados só é possível com as ferramentas e a bateria prontas. Resultado da T1.8: o 1.7b é cerca de 2 vezes mais rápido (~41 contra ~19 [tokens](docs/glossario.md#token) por segundo) e ocupa cerca de metade da memória (1,7 contra 3,2 GB), mas comete erros de português e de conteúdo que o 4B não comete. Nele, desligar o [modo raciocínio](docs/glossario.md#thinking) funciona — o alerta da D25 não se confirmou.
- **Descartado:** mover a T11.5 inteira para o E01 — a parte de qualidade não pode ser feita antes do E09.

---

## Pendências de decisão

Decisões já identificadas, ainda não tomadas (viram entradas datadas quando forem resolvidas):

- Versionar ou não o arquivo `desafio.sqlite` no repositório (tarefa T1.4).
- Qual modelo usar como principal na demonstração — depende do placar da bateria de avaliação (T9.5), das medições de tempo (T11.3) e do teste de memória com o Google Meet aberto (T11.6).
- Levar ou não o modelo reserva `qwen3:1.7b` para a apresentação (T11.5).
