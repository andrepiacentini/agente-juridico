# Glossário

Termos técnicos usados no [`DECISOES.md`](../DECISOES.md), no [roadmap](../project/ROADMAP.md) e no [`plan.md`](plan.md), explicados em linguagem simples. Em ordem alfabética.

---

<a id="agente"></a>
### Agente (de IA)
Programa em que um modelo de linguagem não só responde, mas **decide que ações tomar** — por exemplo, qual consulta fazer no banco — antes de responder. É a diferença entre "um chat que conversa" e "um chat que vai buscar a informação".

<a id="alucinacao"></a>
### Alucinação
Quando o modelo de linguagem afirma algo que parece plausível, mas é inventado. No contexto jurídico é o risco mais grave, por isso o projeto exige citação da fonte e respostas "não consta".

<a id="api"></a>
### API e chave de API
Porta de entrada de um serviço na internet para programas, e não para pessoas: é por ela que o agente manda a pergunta ao modelo em nuvem e recebe a resposta. A **chave de API** é a senha que identifica quem está chamando; fica no arquivo `.env`, nunca no código.

<a id="arquitetura-em-camadas"></a>
### Arquitetura em camadas
Organização do programa em partes empilhadas, cada uma com um papel: acesso ao banco, regras do negócio, agente e tela. Cada parte só usa a que está abaixo dela, o que permite trocar a tela sem mexer nas regras.

<a id="autorizador"></a>
### Autorizador do SQLite
Função que o [SQLite](#sqlite) consulta antes de cada operação de uma consulta, perguntando "posso?". No projeto, durante a consulta livre, ela responde sim só para leitura e nega todo o resto — é a segunda camada de proteção do [SQL](#sql) livre, por baixo da validação do texto e por cima da conexão [somente leitura](#somente-leitura).

<a id="banco-vetorial"></a>
### Banco vetorial
Tipo de banco de dados feito para guardar [embeddings](#embedding) e achar "o que é parecido com isto". Exemplos: Qdrant, Chroma. Foi considerado e descartado neste projeto.

<a id="branch"></a>
### Branch (ramo do Git)
Linha de trabalho paralela dentro do repositório: uma cópia do código em que se pode mexer sem afetar a versão principal (`main`). Quando o trabalho fica pronto, ele é incorporado de volta.

<a id="bytecode"></a>
### Bytecode (cache do Python)
Versão pré-traduzida de um arquivo de código que o [Python](#python) guarda para não traduzi-lo de novo a cada execução. Ele decide se a cópia guardada ainda vale pelo tamanho e pela hora do arquivo; duas versões gravadas no mesmo segundo com o mesmo tamanho o enganam (D31).

<a id="cache-de-prompt"></a>
### Cache do modelo (entrada reaproveitada)
Quando duas chamadas seguidas ao modelo começam com o mesmo texto (as instruções e o histórico da conversa), o modelo pode reaproveitar o trabalho já feito sobre esse começo em vez de lê-lo de novo. No modelo local isso acontece no [KV cache](#kv-cache) do [Ollama](#ollama); nos modelos em nuvem, o fornecedor cobra mais barato pelos [tokens](#token) reaproveitados.

<a id="chainlit"></a>
### Chainlit
Biblioteca Python que cria uma tela de chat no navegador com poucas linhas de código. Mostra, além da resposta, cada passo que o agente deu.

<a id="chunking"></a>
### Chunking (fatiamento)
Cortar documentos longos em pedaços menores para caberem no [RAG](#rag). Aqui é desnecessário (cada documento é curto) e prejudicial (pode cortar uma sentença no meio da fundamentação).

<a id="ci"></a>
### CI (integração contínua) / GitHub Actions
Servidor que, a cada mudança enviada ao GitHub, instala o projeto do zero e roda os [testes](#teste-automatizado) automaticamente. O resultado aparece no [pull request](#pull-request) como um "check" verde ou vermelho. GitHub Actions é o serviço do GitHub que faz isso.

<a id="claude-md"></a>
### CLAUDE.md e AGENTS.md
Arquivos de instruções que o assistente de IA lê sozinho ao começar a trabalhar no projeto: regras, comandos e decisões que ele precisa respeitar. O `CLAUDE.md` é lido pelo Claude Code; o `AGENTS.md` é um padrão aberto lido por várias outras ferramentas. Aqui o conteúdo fica só no `AGENTS.md` e o `CLAUDE.md` o importa.

<a id="clean-code"></a>
### Clean Code
Livro de Robert C. Martin ("Uncle Bob") com regras para escrever código fácil de ler: nomes que dizem o que a coisa faz, funções pequenas que fazem uma coisa só, comentários que explicam o porquê.

<a id="cli"></a>
### CLI / terminal
Interface de texto, sem janelas: o usuário digita, o programa responde na mesma tela preta. É a forma mais simples de rodar o agente e serve de plano B na demo.

<a id="commit"></a>
### Commit, merge e clone (Git)
Três operações do Git. **Commit:** gravar um conjunto de mudanças no histórico, com uma mensagem. **Merge:** juntar o trabalho de uma [branch](#branch) em outra, o que acontece quando um [pull request](#pull-request) é aprovado. **Clone:** copiar o repositório inteiro, com o histórico, para outra pasta ou outra máquina.

<a id="contexto"></a>
### Contexto (janela de contexto)
Quantidade máxima de texto que o modelo consegue "ter em mente" de uma vez — instruções, histórico da conversa e dados consultados, somados. Medida em [tokens](#token). Modelos pequenos têm janelas menores.

<a id="cota"></a>
### Cota (limite de uso de uma API)
Quantidade máxima de pedidos que um fornecedor aceita de uma conta num período — por minuto ou por dia. No plano gratuito do Gemini, a cota medida foi de 20 pedidos por dia (D42); passar dela gera o [erro 429](#erro-http).

<a id="ddd"></a>
### DDD (design dirigido pelo domínio)
Organizar o código com os mesmos conceitos e nomes do assunto tratado — aqui, processo, parte, movimentação, sentença. Quem conhece o domínio jurídico reconhece a estrutura do programa.

<a id="doze-fatores"></a>
### 12 fatores
Conjunto de boas práticas para aplicações modernas. A principal aqui: configurações (modelo, chaves, caminhos) ficam fora do código, em [variáveis de ambiente](#variavel-de-ambiente).

<a id="docstring"></a>
### Docstring
Texto de explicação escrito logo abaixo do nome de uma função no [Python](#python). Nas [ferramentas](#ferramenta) do agente, a docstring é o que o modelo lê para decidir quando usar cada uma e o que cada parâmetro espera.

<a id="embedding"></a>
### Embedding
Conversão de um texto em uma lista de números que representa o seu "significado", permitindo achar textos parecidos. Funciona bem para ideias; funciona mal para códigos exatos, como número de processo.

<a id="endpoint"></a>
### Endpoint (compatível com OpenAI)
Endereço específico dentro de uma [API](#api) para uma operação, como "conversar com o modelo". O [Ollama](#ollama) oferece um endpoint no mesmo formato da API da OpenAI, e é por ele que o [Pydantic AI](#pydantic-ai) fala com o modelo local — o que permite trocar de fornecedor sem mudar o código, mas também limita as opções que podem ser passadas por pedido (D77).

<a id="erro-http"></a>
### Erros 429 e 503
Códigos de resposta de um serviço na internet. **429:** "pedidos demais" — a [cota](#cota) ou o limite por minuto foi ultrapassado. **503:** "serviço indisponível" — o fornecedor está sobrecarregado. Os dois são temporários, e por isso o agente espera alguns segundos e tenta de novo, avisando o usuário (D41).

<a id="ferramenta"></a>
### Ferramenta (tool calling)
Função do programa que o modelo pode pedir para executar, como `buscar_processo(numero)`. O modelo escolhe a ferramenta e os parâmetros; **o código executa** e devolve o resultado. É assim que o modelo consulta o banco sem ter acesso direto a ele.

<a id="framework"></a>
### Framework (biblioteca de agentes)
Conjunto de código pronto que resolve a parte repetitiva de um tipo de programa. Aqui: o "laço" pergunta → escolha de ferramenta → execução → resposta. Exemplos: [Pydantic AI](#pydantic-ai), LangChain.

<a id="fts5"></a><a id="fts"></a>
### FTS5 (busca por palavras)
Recurso que já vem dentro do [SQLite](#sqlite) para buscar palavras em textos longos com rapidez — como o "localizar" de um editor, mas em milhares de documentos ao mesmo tempo.

<a id="golden-set"></a>
### Golden set (bateria de avaliação)
Lista fixa de perguntas com o que a resposta certa deve conter. Roda-se sempre que algo muda, para saber se o agente melhorou ou piorou.

<a id="gpu"></a>
### GPU
Placa de processamento gráfico, o tipo de chip em que os [modelos de linguagem](#llm) rodam rápido. No MacBook M1 o modelo local usa a parte gráfica do próprio chip; um servidor próprio para um modelo maior precisa de uma GPU dedicada, como a NVIDIA L40S usada como referência de custo (D76).

<a id="hash"></a>
### Hash (impressão digital de arquivo)
Código calculado a partir do conteúdo de um arquivo. Se um único byte mudar, o código muda. Serve para provar que o banco não foi alterado.

<a id="homonimo"></a>
### Homônimo
Pessoas diferentes com o mesmo nome. No banco há 643 nomes nessa situação, distinguíveis pelo CPF/CNPJ.

<a id="join"></a>
### JOIN
Comando [SQL](#sql) que junta informações de tabelas diferentes — por exemplo, o processo com o nome do seu magistrado, que fica em outra tabela.

<a id="formatos"></a>
### JSON, YAML, TOML e Markdown
Formatos de arquivo de texto usados no projeto. **JSON:** dados estruturados para programas (as respostas da bateria de avaliação). **YAML:** dados estruturados legíveis por pessoas (os casos da bateria, `golden.yaml`). **TOML:** configuração (o `pyproject.toml` e a tabela de preços `prices.toml`). **Markdown:** texto com títulos, listas e tabelas, como este glossário e o `DECISOES.md`.

<a id="kiss-yagni-dry"></a>
### KISS, YAGNI e DRY
Três lemas de simplicidade. **KISS** ("mantenha simples"): a solução mais simples que funciona. **YAGNI** ("você não vai precisar disso"): não construir nada antes de haver necessidade real. **DRY** ("não se repita"): cada regra escrita em um lugar só.

<a id="kv-cache"></a>
### KV cache
Memória de trabalho que o modelo usa durante a conversa, proporcional ao tamanho do [contexto](#contexto). Pode ser comprimida (`q8_0`) para ocupar menos [RAM](#ram).

<a id="langchain"></a>
### LangChain / LlamaIndex
[Frameworks](#framework) populares para aplicações com IA. Foram descartados por terem muitas camadas de abstração (difíceis de explicar) e por serem centrados em [RAG](#rag).

<a id="latencia"></a>
### Latência
Tempo entre enviar a pergunta e receber a resposta. Meta do projeto: menos de 30 segundos no modelo local.

<a id="launchctl"></a>
### launchctl e LaunchAgent (macOS)
`launchctl` é o comando do macOS que controla programas de fundo e as [variáveis de ambiente](#variavel-de-ambiente) que os aplicativos herdam ao abrir. Um **LaunchAgent** é um arquivo de configuração que o macOS executa a cada login; o projeto usa um para fixar a compressão do [KV cache](#kv-cache) do [Ollama](#ollama) (D77).

<a id="llm"></a>
### LLM (modelo de linguagem)
O "cérebro" do chat: um programa treinado em muito texto que entende e produz linguagem. Exemplos: Qwen, Claude, GPT. O tamanho é medido em bilhões de parâmetros (ex.: "4B" = 4 bilhões); maior tende a ser melhor, mas exige mais memória.

<a id="metadados"></a>
### Metadados
Dados *sobre* um documento, não o documento em si: tipo, data, autor, número de páginas. O agente vê primeiro os metadados e só depois decide qual texto ler.

<a id="minuta"></a>
### Minuta de sentença
Rascunho de uma decisão judicial. No projeto, é sempre identificada como **proposta** e nunca como sentença proferida.

<a id="instruct"></a>
### Modelo instruct
Variante de um modelo de linguagem treinada para responder direto a instruções, sem o [modo raciocínio](#thinking). O modelo local do projeto, `qwen3:4b-instruct-2507`, é dessa variante (D25).

<a id="modelo-local"></a>
### Modelo local × modelo em nuvem
**Local:** roda no próprio computador (via [Ollama](#ollama)), sem internet e sem enviar dados para fora. **Nuvem:** roda nos servidores do fornecedor (ex.: Gemini, do Google, ou Claude, da Anthropic), é mais capaz, mas exige internet e envia os dados.

<a id="thinking"></a>
### Modo raciocínio (thinking)
Recurso de alguns modelos (como o Qwen3) de "pensar em voz alta" antes de responder. Melhora tarefas difíceis, mas deixa a resposta bem mais lenta.

<a id="moe"></a>
### MoE (mistura de especialistas)
Arquitetura de [modelo de linguagem](#llm) dividida em muitos blocos ("especialistas"), dos quais só alguns trabalham em cada [token](#token). Um MoE de 26B com 4B ativos ocupa a [RAM](#ram) de um modelo de 26B, mas gera texto com a velocidade de um de 4B. Por isso é a opção natural para modelos maiores num Mac (D91).

<a id="movimentacao"></a>
### Movimentação processual
Cada registro do andamento do processo (distribuição, citação, sentença…), com código e data. Existe mesmo nos processos sem documentos.

<a id="multi-turno"></a>
### Multi-turno
Conversa com várias perguntas seguidas em que o sistema lembra do que já foi dito.

<a id="numero-cnj"></a>
### Número CNJ
Formato padrão nacional do número de processo: `NNNNNNN-DD.AAAA.J.TR.OOOO` (ex.: `0000007-79.2023.8.99.9014`).

<a id="observabilidade"></a>
### Observabilidade (logs estruturados)
Capacidade de ver o que o programa fez. Cada chamada de [ferramenta](#ferramenta) grava um registro com nome, parâmetros, tempo gasto e quantidade de resultados, em formato fácil de filtrar.

<a id="ollama"></a>
### Ollama
Programa que baixa e roda [modelos de linguagem](#llm) no próprio computador.

<a id="omlx"></a>
### oMLX
Programa que roda [modelos de linguagem](#llm) no Mac usando o MLX, a biblioteca da Apple para os chips M1 e seguintes. Faz o mesmo papel do [Ollama](#ollama), só que exclusivo para Mac. Foi testado no projeto e não virou padrão (D89).

<a id="plotly"></a>
### Plotly
Biblioteca [Python](#python) que desenha gráficos interativos para páginas web. O [Chainlit](#chainlit) sabe mostrá-los dentro da conversa, e é assim que o painel de consumo exibe custo por modelo, tokens por tipo de pergunta e custo acumulado (D75).

<a id="pressao-de-memoria"></a>
### Pressão de memória (swap)
Indicador do Monitor de Atividade do Mac que mostra se a [RAM](#ram) está dando conta: verde é folga; amarelo e vermelho indicam que o sistema começou a usar o disco como memória extra (*swap*). O disco é muito mais lento que a RAM, então tudo fica lento — principalmente o [modelo local](#modelo-local).

<a id="ptax"></a>
### PTAX
Taxa de câmbio oficial calculada pelo Banco Central do Brasil a cada dia útil, a partir das cotações do mercado. O projeto usa a PTAX de venda, com a data, para converter os preços em dólar dos modelos para reais (D73).

<a id="pull-request"></a>
### Pull request
Pedido para incorporar o trabalho de uma [branch](#branch) em outra, com a lista do que mudou. É o momento de revisar antes de juntar.

<a id="pydantic-ai"></a>
### Pydantic AI
[Framework](#framework) Python escolhido para o agente. Transforma funções comuns em [ferramentas](#ferramenta) e funciona igual com modelos locais e de nuvem.

<a id="python"></a>
### Python
Linguagem de programação do projeto. Já traz o [SQLite](#sqlite) embutido e tem o ecossistema de bibliotecas de IA mais maduro.

<a id="quantizacao"></a>
### Quantização (Q4)
Técnica que "comprime" um modelo guardando seus números com menos precisão. Um modelo de 4B quantizado em Q4 ocupa ~2,6 GB em vez de ~8 GB, com pequena perda de qualidade.

<a id="rag"></a>
### RAG (geração aumentada por recuperação)
Técnica comum em chats com IA: os documentos são [fatiados](#chunking), convertidos em [embeddings](#embedding) e guardados num [banco vetorial](#banco-vetorial); a cada pergunta, buscam-se os trechos "mais parecidos" e entregam-se ao modelo. Bom para textos soltos; inadequado aqui (ver `DECISOES.md`).

<a id="ram"></a>
### RAM
Memória do computador usada pelos programas em execução. O MacBook do projeto tem 8 GB, e o modelo de IA precisa caber nela junto com o resto do sistema.

<a id="solid"></a>
### SOLID
Cinco princípios de organização de código orientado a objetos. Os mais usados aqui: cada parte tem uma única responsabilidade, e as partes dependem de "contratos" e não de peças concretas — é o que permite trocar o modelo de IA sem mexer no agente.

<a id="somente-leitura"></a>
### Somente leitura
Modo de abrir o banco em que é possível consultar, mas é impossível alterar ou apagar. Garantido pelo próprio SQLite, não pelo modelo.

<a id="sql"></a>
### SQL
Linguagem padrão para consultar bancos de dados. Ex.: `SELECT nome FROM parte WHERE id = 10` = "traga o nome da parte número 10".

<a id="sqlite"></a>
### SQLite
Banco de dados que é um único arquivo (`desafio.sqlite`), sem servidor. Já vem embutido no Python.

<a id="sqlite-vec"></a>
### sqlite-vec
Extensão que adiciona busca por semelhança ([embeddings](#embedding)) dentro do próprio arquivo SQLite. É o caminho futuro caso busca por "significado parecido" vire requisito.

<a id="system-prompt"></a>
### System prompt (instruções do agente)
Texto fixo enviado ao modelo antes de cada conversa com seu papel e suas regras ("responda em português", "cite a fonte", "diga quando não houver dado").

<a id="tabela-temporaria"></a>
### Tabela temporária (TEMP)
Tabela criada na memória durante a execução e descartada ao fechar. Permite montar índices de busca sem alterar o arquivo do banco.

<a id="tdd"></a>
### TDD (desenvolvimento guiado por testes)
Escrever primeiro o [teste](#teste-automatizado) que descreve o comportamento esperado e só depois o código que o faz passar. Aqui, cada armadilha do banco vira um teste antes de ser tratada.

<a id="teste-automatizado"></a>
### Teste automatizado (pytest)
Código que verifica se outro código funciona, rodado com um comando (`uv run pytest`). As ferramentas do agente são testadas sem usar IA, porque o resultado delas é sempre o mesmo.

<a id="text-to-sql"></a>
### Text-to-SQL
Abordagem em que o modelo escreve a consulta [SQL](#sql) inteira a partir da pergunta. Modelos pequenos erram com frequência (inventam colunas, esquecem regras), por isso aqui é só uma "válvula de escape".

<a id="thread"></a>
### Thread
Linha de execução dentro de um programa; um programa pode ter várias trabalhando ao mesmo tempo. Importa aqui porque a conexão com o [SQLite](#sqlite) só pode ser usada pela thread que a abriu — por isso as [ferramentas](#ferramenta) do agente são escritas para rodar sempre na mesma (D67).

<a id="timeout"></a>
### Timeout / LIMIT
**Timeout:** tempo máximo que uma consulta pode rodar antes de ser interrompida. **LIMIT:** número máximo de linhas que uma consulta pode devolver. Travas contra consultas pesadas.

<a id="token"></a>
### Token
Unidade de texto que o modelo processa — em português, em média, pouco menos de uma palavra. Usado para medir o tamanho do [contexto](#contexto).

<a id="tokens-por-segundo"></a>
### Tokens por segundo (tok/s)
Velocidade do modelo: quantos [tokens](#token) ele lê ou escreve em um segundo. Ler o pedido (as instruções e os documentos) é muito mais rápido do que escrever a resposta; no modelo local, a leitura ficou em ~120 tok/s e a escrita em 6 a 9 tok/s (D78).

<a id="uv"></a>
### uv
Ferramenta que prepara o ambiente do projeto com um único comando (`uv sync`): baixa a versão certa do [Python](#python) e instala as bibliotecas exatamente nas versões registradas no projeto (arquivo `uv.lock`). Assim o programa roda igual na máquina do autor e na da banca, sem instalação manual. Faz o papel do `pip` e do `venv` juntos, bem mais rápido.

<a id="validador-de-resposta"></a>
### Validador da resposta
Conferência feita por código depois que o modelo responde e antes de a resposta chegar ao usuário. Se a regra não for cumprida, a resposta volta ao modelo com o motivo, e ele tenta de novo. Aqui, garante que todo número de processo citado na pergunta tenha sido consultado no banco antes de o agente afirmar qualquer coisa sobre ele. Serve para regras que o modelo pequeno não segue só com as [instruções](#system-prompt).

<a id="variavel-de-ambiente"></a>
### Variável de ambiente (`.env`)
Configuração guardada fora do código, num arquivo `.env`. Permite trocar o modelo (ou guardar uma chave de acesso) sem mexer no programa.
