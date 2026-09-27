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

### D27 — O banco `desafio.sqlite` fica no repositório
- **Decisão:** manter o arquivo `desafio.sqlite` (40 MB) versionado no Git, como já estava desde o primeiro commit. O projeto nunca o altera ([somente leitura](docs/glossario.md#somente-leitura), D04). Impressão digital ([hash](docs/glossario.md#hash) SHA-256) do arquivo nesta data, para a verificação da T2.3: `8a90b47cdc3b07bcb395ffe0e81c3d56dd33946fa047dec7dc86499767690c43`.
- **Por quê:** a banca clona o repositório e roda o projeto sem baixar, descompactar ou posicionar o arquivo à mão — é o que o E01 promete. São dados fictícios, sem sigilo, o repositório é privado, e 40 MB está bem abaixo dos limites do GitHub (aviso a partir de 50 MB, bloqueio a partir de 100 MB).
- **Descartado:** tirar o arquivo do Git e instruir o download no README (o edital distribui um ZIP de 7,1 MB). Acrescentaria um passo manual para a banca; e, como o arquivo já está no histórico, removê-lo agora não diminuiria o repositório sem reescrever esse histórico.

### D28 — Apresentação presencial: teste com videochamada vira opcional
- **Decisão:** a tarefa T11.6 (medir a memória com o Google Meet aberto) passa a ser opcional. Só será feita se a apresentação deixar de ser presencial; caso contrário, é cancelada no fim do E11. Continua valendo a regra da D22: Chainlit no Safari, só com a aba do chat.
- **Por quê:** o edital diz que a apresentação é **presencial** ("Sessão de Demonstração e Arguição Técnica"). A D22 partiu de uma apresentação remota, que não é o cenário previsto. Sem videochamada, a conta de memória do `plan.md` §5 volta a ter folga.
- **Uso de IA:** o Claude Code encontrou a informação ao reler o edital durante a T1.4; a D22 tinha sido escrita sem conferir esse ponto.

### D29 — Pydantic AI "enxuto", só com os provedores usados; Python travado na 3.12
- **Decisão:** instalar `pydantic-ai-slim[openai,anthropic]` em vez do pacote completo `pydantic-ai`, e declarar o projeto como compatível só com Python 3.12 (`>=3.12,<3.13`).
- **Por quê:** o pacote completo traz bibliotecas de todos os fornecedores de IA (Google, Groq, Mistral, Cohere, AWS e outros), que o projeto não usa. A versão enxuta instala só o necessário: o conector compatível com OpenAI, usado pelo [Ollama](docs/glossario.md#ollama), e o da Anthropic. Menos dependências significa instalação mais rápida e menos coisa para dar errado na máquina da banca. A trava na 3.12 evita que o [uv](docs/glossario.md#uv) escolha o Python 3.14 do sistema (D07). Verificado: `uv sync` limpo termina sem erro, Python 3.12.14, SQLite 3.53.1 com [FTS5](docs/glossario.md#fts5), e o Pydantic AI 2.50 reconhece `ollama:qwen3:4b-instruct-2507-q4_K_M`.
- **Descartado:** o pacote completo `pydantic-ai`, previsto no plano original.

## 26/09/2026

### D30 — Gemini 3.8 Flash, no plano gratuito, como alternativa em nuvem; Claude vira opção
- **Decisão:** a alternativa em nuvem ao [modelo local](docs/glossario.md#modelo-local) passa a ser o Gemini 3.8 Flash (`google:gemini-3.8-flash`), usado pelo plano gratuito do Google AI Studio. O Claude (`anthropic:claude-sonnet-5`) continua configurado como opção, para quando houver crédito na conta da Anthropic. O conector do Google foi acrescentado ao Pydantic AI (`pydantic-ai-slim[openai,anthropic,google]`), a chave vai no `.env` como `GOOGLE_API_KEY`, e o teste do Claude virou a tarefa opcional T1.10.
- **Por quê:** a API da Anthropic recusou a primeira chamada por falta de crédito, e a assinatura do app Claude não inclui uso da API. O Google oferece um plano gratuito da API, sem cartão, que inclui o `gemini-3.8-flash` — suficiente para o experimento e para a comparação entre modelos. A troca não mexe em nenhuma linha de código, só na [variável de ambiente](docs/glossario.md#variavel-de-ambiente) `LLM_MODEL`: é a portabilidade prometida na D08 funcionando na prática.
- **Limites do plano gratuito:** o Google pode usar o conteúdo enviado para melhorar seus produtos (não há problema aqui: os dados do desafio são fictícios; com dados reais, o caminho continua sendo o modelo local ou o plano pago). O número máximo de chamadas por minuto não é publicado na documentação; como cada pergunta ao agente vira várias chamadas, isso será medido quando o agente e a bateria de avaliação estiverem prontos.
- **Resultado do teste (T1.9):** o Gemini deu a melhor resposta dos modelos testados — correta, completa e sem erro de conteúdo —, em 3 a 4 segundos no modo padrão. Dois cuidados para quando o agente usar o Gemini: o limite de tokens de saída inclui o [raciocínio](docs/glossario.md#thinking) (com limite de 400, ele gastou 383 pensando e cortou a resposta), então o nível de raciocínio deve ser fixado em `low`; e o plano gratuito oscila — uma chamada recusada por "alta demanda" e tempos de 2,7 a 20,3 segundos na mesma pergunta. Números completos no comparativo do `plan.md` §5.
- **Descartado:** colocar crédito na Anthropic agora (custo sem necessidade para o experimento); usar os créditos mensais do Google AI Pro (exigem ativar um programa à parte, e o plano gratuito basta); tirar o conector da Anthropic (custaria pouco mantê-lo e ele permite mostrar três fornecedores na apresentação).

### D31 — Erro do assistente: um contra-teste alterou o banco original
- **O que aconteceu:** na T2.2, para provar que os testes de escrita realmente detectam o problema, o Claude Code trocou por um instante o modo somente leitura (`mode=ro`) por leitura e escrita (`mode=rw`), rodou os testes contra uma **cópia** do banco e depois restaurou o arquivo. Na rodada seguinte, já com o código correto, os testes escreveram no `desafio.sqlite` **original**: o Python continuou executando a versão alterada guardada em cache (*bytecode*). As duas versões tinham o mesmo tamanho e foram gravadas no mesmo segundo, e o Python usa justamente tamanho e horário para decidir se o cache ainda vale.
- **Como foi corrigido:** o arquivo foi restaurado pelo Git (D27) e a [impressão digital](docs/glossario.md#hash) conferida com a referência registrada — idêntica. O cache foi apagado e os testes voltaram a passar sem tocar no banco.
- **Decisão:** contra-testes que desligam proteções só são feitos numa cópia completa do projeto, em outra pasta — nunca na pasta de trabalho. E a verificação da impressão digital do banco (T2.3) passa a ser o próximo passo, para que um erro assim seja detectado automaticamente a cada rodada de testes.
- **Por quê:** a proteção "somente leitura" funcionou (D04); o que falhou foi o procedimento do teste, que desligou a proteção dentro da pasta real. É também a prova de valor de duas decisões anteriores: versionar o banco (D27) permitiu restaurá-lo em segundos, e o hash de referência permitiu provar que a restauração foi exata.
- **Uso de IA:** erro do Claude Code, identificado por ele mesmo ao ver o banco listado como alterado no Git, com a causa confirmada inspecionando o cache.

### D32 — Índice de busca montado uma vez por sessão, e não a cada conexão
- **Decisão:** o índice de busca por palavras ([FTS5](docs/glossario.md#fts5)) é criado pela função `create_search_index`, separada da função que abre o banco, e chamado uma vez no início de cada sessão do agente. Ele fica em [tabelas temporárias](docs/glossario.md#tabela-temporaria) e ignora acentos e maiúsculas ("onus" encontra "Ônus").
- **Por quê:** a tarefa previa montar o índice "ao conectar". Medido, ele leva 0,35 s para os 25.582 documentos e 14.966 partes — barato para uma sessão de conversa, mas desperdício para quem só precisa ler uma linha, como a maioria dos testes. Separar as duas coisas mantém a conexão rápida e cada função com uma responsabilidade.
- **Descartado:** criar o índice dentro de `connect()` (todo uso do banco pagaria o custo); gravar o índice no arquivo (proibido: o banco é [somente leitura](docs/glossario.md#somente-leitura), D04).

### D33 — Testes na CI a cada pull request (revisa a D15)
- **Decisão:** os [testes automatizados](docs/glossario.md#teste-automatizado) passam a rodar na [integração contínua](docs/glossario.md#ci) do GitHub ([GitHub Actions](docs/glossario.md#ci)) em todo [pull request](docs/glossario.md#pull-request) e em todo envio para a `main`. O servidor instala o projeto do zero com o [uv](docs/glossario.md#uv) e roda a suíte inteira, inclusive a guarda de integridade do banco (T2.3). Um PR só é aceito com o check `tests` verde.
- **Por quê:** a D15 tinha deixado a CI de fora como "custo sem retorno". Com o projeto em andamento, ela passou a se pagar: tira a verificação da máquina de quem desenvolve (um ambiente limpo pega o que "funciona na minha máquina" esconde), deixa a prova visível em cada PR para a banca e custa cerca de 1 minuto por execução, dentro da cota gratuita. Não precisa de nenhuma chave de API, porque os testes não usam IA.
- **Limitação:** no plano gratuito do GitHub, repositório privado não permite bloquear o botão de merge quando o check falha. A regra fica no fluxo de trabalho (`AGENTS.md`): o assistente acompanha o check e avisa o resultado; o autor só faz o merge com ele verde.
- **Descartado:** tornar o repositório público só para liberar o bloqueio automático (o edital pede o acesso ao repositório para os e-mails da banca, e manter o código de um processo seletivo restrito é o mais prudente); assinar o GitHub Pro (custo sem necessidade); medir cobertura de testes (mantido o que a D15 decidiu).

### D34 — Comarcas "divergentes" são a mesma cidade escrita de outro jeito
- **Decisão:** a ferramenta `find_case` avisa quando a comarca do processo e a da vara estão escritas de forma diferente, mas distingue dois casos: **mesma comarca com grafia diferente** ("A comarca está grafada de forma diferente no processo ('S. José') e na vara ('São José')") e **comarca realmente diferente** ("Comarca do processo difere da comarca da vara"). Para classificar, compara os nomes sem acento, sem diferença de maiúsculas e de espaços e com as três abreviações encontradas no banco por extenso (`S.`, `Sto.`, `Bal.`). O valor mostrado é sempre o original: nada é corrigido.
- **Por quê:** a análise inicial (D13) contou 1.024 processos com comarca diferente da vara e tratou isso como divergência. Ao escrever os testes da T3.4, o primeiro exemplo era `CRICIÚMA` × `Criciúma`. Medindo todos: 451 têm espaço sobrando, 296 estão sem acento, 238 diferem só em maiúsculas e 39 usam abreviação — **nenhum é outra cidade**. Avisar "comarca diferente" faria o agente sugerir um problema de competência que não existe, o que seria inventar informação.
- **Descartado:** reportar a diferença literal (enganoso, pelo motivo acima); corrigir o nome da comarca na resposta (a regra do projeto é reportar, nunca corrigir); ignorar as diferenças (esconderia um problema real de qualidade do cadastro).
- **Uso de IA:** o plano escrito com o Claude Code registrou o número sem olhar os exemplos; o próprio Claude Code percebeu o problema no primeiro caso de teste e mediu o banco inteiro antes de implementar.

### D35 — O papel da parte vem do polo do processo, não do cadastro da pessoa
- **Decisão:** a ferramenta `list_parties` agrupa as partes pelo polo do processo (ativo = autores, passivo = réus) e ignora o campo `parte.tipo`. O "tipo" mostrado é pessoa física ou jurídica, deduzido do formato do documento (CPF ou CNPJ). Uma parte vinculada duas vezes ao mesmo polo aparece uma vez só, com um aviso de que o cadastro a repete.
- **Por quê:** `parte.tipo` guarda "autor" ou "réu" no cadastro da pessoa, mas a mesma pessoa pode ser autora num processo e ré em outro. Na análise, esse campo contradiz o polo em 1.633 vínculos (821 "réus" no polo ativo e 812 "autores" no passivo). Mostrar os dois confundiria o modelo; o polo é o dado que vale para aquele processo. Todos os 14.966 documentos seguem o formato de CPF ou de CNPJ, então a dedução de pessoa física ou jurídica é segura.
- **Descartado:** usar `parte.tipo` como papel (erraria em 1.633 casos); mostrar a parte duplicada duas vezes (pareceria que são duas pessoas).

### D36 — Oitava ferramenta: buscar processos por atributo, sem SQL do modelo
- **Decisão:** acrescentar a ferramenta `search_cases` (tarefa T3.11) às sete previstas no plano. Ela recebe filtros prontos — assunto, classe, comarca, vara, magistrado, situação, período e valor — e devolve o total e uma lista compacta de processos.
- **Por quê:** durante a implementação das ferramentas, o autor pediu uma reavaliação de cobertura, já que o edital avisa que "os exemplos não esgotam as perguntas". A análise mostrou que, para perguntas sobre **um** processo, as ferramentas existentes cobrem todas as variações enumeradas (os documentos são curtos: o processo mais pesado soma 14.606 caracteres, e o agente pode lê-lo inteiro). A lacuna estava nas perguntas que **selecionam processos por característica** ("quais processos são sobre plano de saúde?", "quantos o juiz X julgou?"): elas só tinham o [SQL livre](docs/glossario.md#text-to-sql), justamente o caminho em que um modelo pequeno mais erra (D03) — e o índice de busca (T2.5) não cobre assunto nem classe. Com uma ferramenta de filtros, essa família de perguntas sai do caminho frágil, e o SQL livre volta a ser exceção de verdade.
- **Descartado:** ampliar o índice de busca por palavras para assunto e classe (resolveria só a busca por texto, não filtros por data, valor, juiz ou situação); confiar apenas no SQL livre (risco de coluna inventada ou regra do banco esquecida).
- **Uso de IA:** a análise de cobertura foi feita pelo Claude Code a pedido do autor, enumerando famílias de perguntas contra o perfil real do banco; a lacuna e a ferramenta foram propostas pela IA e aprovadas pelo autor.

### D37 — O lado de cada advogado é deduzido pelas peças que só um lado apresenta
- **Decisão:** a ferramenta `list_documents` identifica que lado cada advogado representa. Peças que só o autor apresenta (petição inicial, réplica, emenda à inicial) e peças que só o réu apresenta (contestação, exceção de pré-executividade, embargos à execução fiscal) definem o lado; as demais peças — manifestações, apelação, contrarrazões — herdam o lado pelo número da OAB de quem assinou. A ferramenta também avisa quando a OAB cadastrada como autora do documento não aparece entre as assinaturas do texto, e quando um mesmo advogado assina peças dos dois lados.
- **Por quê:** o banco não tem tabela de advogados; eles só aparecem no campo de autor dos documentos. A pergunta 2 do edital pede "os advogados do processo", e dizer quem representa quem é o que torna a resposta útil — sem deixar o modelo adivinhar. A regra identifica o lado de todos os advogados do banco (3.683 do autor, 1.831 do réu). Ao conferir a assinatura, apareceu uma armadilha: a petição de acordo é assinada pelos advogados dos dois lados, então comparar só com a última assinatura acusaria 561 divergências falsas; o certo é verificar se a OAB cadastrada está entre as assinaturas (309 divergências reais).
- **Descartado:** deixar o lado para o modelo deduzir lendo os documentos (caro e sujeito a erro num modelo pequeno); comparar o autor cadastrado só com a última assinatura do texto (falso positivo em toda petição de acordo).

### D38 — Busca de pessoas numa ferramenta própria; a pessoa é o CPF/CNPJ
- **Decisão:** a busca de partes pelo nome virou uma ferramenta separada, `search_parties`, em vez de um modo da busca de termos nos documentos. Ela agrupa os resultados por CPF/CNPJ — cada documento é uma pessoa —, lista os processos e o polo de cada uma e, quando há mais de uma pessoa, avisa o agente para perguntar de qual se trata.
- **Por quê:** buscar pessoas e buscar termos têm entradas e respostas diferentes (pessoas com processos × trechos de documentos); juntar as duas numa ferramenta só confundiria um modelo pequeno na hora de escolher e de ler a resposta. Agrupar pelo documento resolve os 643 nomes homônimos, que viram pessoas separadas. A análise mostrou também o problema inverso: 332 CPFs/CNPJs aparecem no cadastro com mais de um nome — às vezes erro de digitação ("Imobiliária Mendes" × "Mendez"), às vezes empresas completamente diferentes com o mesmo CNPJ. A ferramenta não tem como saber qual é o caso, então mostra todos os nomes e avisa, sem escolher.
- **Descartado:** agrupar por nome (juntaria pessoas diferentes); escolher um dos nomes quando o documento tem vários (seria corrigir o cadastro por palpite).

## 27/09/2026

### D39 — Terceira camada de proteção no SQL livre: o autorizador do próprio SQLite
- **Decisão:** a consulta livre (`run_sql`) é protegida em três camadas, e não duas como previa o plano: (1) a validação do texto aceita um único comando de leitura; (2) enquanto a consulta roda, um **autorizador** do SQLite — uma função que o banco consulta antes de cada operação — permite só leitura e funções e nega todo o resto; (3) a conexão é [somente leitura](docs/glossario.md#somente-leitura) (D04). A única exceção no autorizador é o `PRAGMA data_version`, uma leitura de contador que o índice de busca ([FTS5](docs/glossario.md#fts5)) faz por dentro.
- **Por quê:** validar texto sempre tem brechas (comentários, formas pouco usuais de escrever um comando); o autorizador decide pelo que o banco realmente vai fazer, não pelo texto. A conexão somente leitura já impede escrita no arquivo, mas não impede tudo — por exemplo, criar tabelas temporárias ou anexar outro arquivo; o autorizador cobre isso. Ao testar, a primeira versão bloqueou até a busca no índice de palavras; registrando as operações pedidas, apareceu a leitura do `data_version`, liberada de forma exata (sem valor atribuído) — `PRAGMA data_version = 5` continua negado.
- **Descartado:** confiar só na validação do texto (brechas); confiar só na conexão somente leitura (não barra tabelas temporárias nem anexos); liberar pragmas em geral para o índice funcionar.

### D40 — Primeiro teste de ponta a ponta com o modelo local: acerta a ferramenta e os dados, falta citar a fonte
- **Decisão:** registrar o resultado do primeiro teste real (T5.6) e levar os dois problemas encontrados para as tarefas que já existem: a citação de dados do cadastro para a T7.7 e o tamanho do contexto do modelo para a T11.1.
- **Resultado:** a pergunta "Quem são as partes do processo 0000007-79.2023.8.99.9014?" foi feita 3 vezes ao [modelo local](docs/glossario.md#modelo-local) (`qwen3:4b-instruct-2507`), cada vez numa conversa nova. Nas 3, o agente escolheu a [ferramenta](docs/glossario.md#ferramenta) certa (`list_parties`), trouxe as partes corretas — autor João Ziegler Rocha (pessoa física, com CPF) e réu Operadora de Saúde Cambirela Ltda (pessoa jurídica, com CNPJ) — e informou que não havia avisos no cadastro. Tempo: 35 s na primeira (modelo ainda "frio"), 13–14 s nas seguintes; duas chamadas ao modelo por pergunta (uma para escolher a ferramenta, outra para redigir), ~6 mil [tokens](docs/glossario.md#token) de entrada no total.
- **Por quê registrar os problemas, e não corrigir agora:** (1) nenhuma das respostas citou a fonte. As instruções só ensinam a citar documento e movimentação, e as partes vêm do cadastro do processo — o modelo não tinha formato para usar; é uma lacuna da regra, tratada na T7.7 (citação obrigatória), com um formato para dados do cadastro. (2) O Ollama estava usando uma [janela de contexto](docs/glossario.md#contexto) de 4.096 tokens, e só as instruções e as descrições das ferramentas ocupam ~2.900. Nesta pergunta coube; num resumo, com documentos lidos, o excesso seria cortado sem aviso. A T11.1 já prevê subir o contexto para 16 mil tokens.
- **Uso de IA:** o Claude Code rodou o teste 3 vezes em vez de uma, porque o modelo não responde sempre igual, e notou o limite de contexto na saída do Ollama.

### D41 — Mesma pergunta no Gemini: igual no acerto, duas vezes mais rápido, instável no plano gratuito
- **Decisão:** registrar a comparação da T5.7 como base para a escolha do modelo da demonstração (pendência já listada) e tratar as recusas temporárias do plano gratuito antes da apresentação.
- **Resultado:** a pergunta da D40 foi repetida 3 vezes com o Gemini 3.8 Flash, trocando apenas o `.env` (`LLM_MODEL=google:gemini-3.8-flash`, `LLM_THINKING=low`) — **nenhuma linha de código mudou**. O Gemini acertou a ferramenta e as partes nas 3 vezes, como o modelo local, em 6 a 11 segundos por pergunta (o local levou 35 s na primeira e 13–14 s nas seguintes), e em 2 das 3 respostas citou a fonte por conta própria, num formato improvisado. Em compensação, na primeira rodada o serviço recusou o pedido duas vezes com erro 503 ("alta demanda") e a resposta só veio na terceira tentativa, cerca de 27 segundos depois.

  | | Modelo local | Gemini 3.8 Flash |
  |---|---|---|
  | Ferramenta e dados corretos | 3/3 | 3/3 |
  | Tempo por pergunta | 35 s (1ª) · 13–14 s | 6–11 s |
  | Cita a fonte | 0/3 | 2/3, formato próprio |
  | Recusas do serviço | 0 | 2 (503) |

- **Por quê:** a troca só por configuração é a portabilidade prometida na D08 funcionando de ponta a ponta. A velocidade favorece o Gemini numa apresentação; a instabilidade do plano gratuito favorece o local. Sem tratamento, uma recusa aparece para a banca como falha. Repetir automaticamente os pedidos recusados temporariamente, com uma espera curta, resolve a maior parte dos casos e vale para qualquer provedor.
- **Uso de IA:** o autor observou que o modelo local estava lento e pediu para seguir com o teste no Gemini; o Claude Code contou as recusas do serviço em vez de apenas repetir até funcionar, porque a taxa de falhas também é dado para a decisão.

---

## Pendências de decisão

Decisões já identificadas, ainda não tomadas (viram entradas datadas quando forem resolvidas):

- Qual modelo usar como principal na demonstração — depende da comparação da D41 (Gemini duas vezes mais rápido, mas com recusas no plano gratuito), do placar da bateria de avaliação (T9.5), das medições de tempo (T11.3) e, se a apresentação passar a ser remota, do teste de memória com o Google Meet aberto (T11.6).
- Levar ou não o modelo reserva `qwen3:1.7b` para a apresentação (T11.5).
