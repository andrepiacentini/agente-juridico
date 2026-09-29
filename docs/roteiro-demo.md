# Roteiro da demonstração

Sequência da apresentação ao vivo, com o que fazer, o que mostrar, o que dizer e o tempo medido no ensaio de 29/09/2026 (D83). Modelo da demonstração: `gemini-3.8-flash` (D71); o modelo local `qwen3:4b` entra num bloco próprio e é o plano B. Tempo total previsto: **12 a 15 minutos**, dos quais cerca de 3 minutos são o modelo trabalhando.

## Antes de começar (10 minutos antes)

1. **Fechar tudo** que não for a demonstração: editor, navegador do dia a dia, mensageiros (D22, D25: com a máquina cheia o modelo local cai de 19 para 2 tokens por segundo).
2. **Ollama aberto**, com *Context length* em 16k (D77). Aquecer o modelo, para a primeira pergunta do bloco local não pagar os 14 s de carga (D78): `ollama run qwen3:4b-instruct-2507-q4_K_M "oi"` e sair.
3. **`.env`** com o modelo da demonstração e o seletor com os dois modelos:

   ```bash
   LLM_MODEL=google:gemini-3.8-flash
   LLM_THINKING=low
   LLM_MODEL_OPTIONS=google:gemini-3.8-flash@low,ollama:qwen3:4b-instruct-2507-q4_K_M
   GOOGLE_API_KEY=...
   ```

4. **Registro de uso limpo**, para o painel "Ver consumo" mostrar só a demonstração: `mv usage.sqlite usage-antes-da-demo.sqlite` (o arquivo é recriado na primeira resposta).
5. **Subir o chat** e deixar o terminal do plano B pronto em outra aba do terminal:

   ```bash
   uv run chainlit run app.py          # abre o Safari em http://localhost:8000
   uv run case-assistant               # plano B, na outra aba; só usar se o navegador falhar
   ```

6. **Uma pergunta de teste** no chat ("qual o assunto do processo 0000007-79.2023.8.99.9014?") e depois **Novo chat**: confirma a chave do Google e aquece a conexão. Apagar de novo o `usage.sqlite` se quiser o painel zerado.
7. Safari só com a aba do chat; nada mais aberto.

## Sequência

Os tempos são os do ensaio (Gemini, uma conversa, histórico acumulado). "Passos" = o bloco "Consultou o banco de dados" abaixo de cada resposta, que se abre para mostrar cada consulta e o que o banco devolveu.

### Abertura (1 min, sem modelo)

Tela inicial com os quatro botões. Dizer: "É um agente que consulta o banco com ferramentas de SQL prontas, sem RAG vetorial, porque toda pergunta do edital parte de um número de processo. Tudo o que ele afirma vem de uma consulta que aparece na tela, e ele diz quando o dado não existe." Apontar o seletor de modelo (engrenagem ao lado do campo) e o botão "Sobre".

### Bloco 1 — as 4 perguntas do edital no processo 3161 (19 documentos) — 48 s de modelo

| # | Ação | O que mostrar | O que dizer | Tempo |
|---|---|---|---|---:|
| 1 | Clicar **Resumo do processo** | Abrir os passos: `find_case`, `list_movements`, `list_documents`, `list_parties`, três `read_document`. Na resposta: citações `[doc 7865 — Petição Inicial, 08/01/2024]`, `[mov. …]`, `[cadastro do processo]`; o aviso de juiz aposentado; o rodapé com tokens, custo e tempo | "Ele vê primeiro o índice dos documentos e lê só os que precisa: metadados primeiro, texto sob demanda. Cada frase cita de onde veio." | 19 s |
| 2 | Clicar **Partes, juiz e advogados** | Advogados com o lado de cada um (autor e ré); o aviso de que os documentos 7872 e 7877 têm assinatura de outra OAB | "Não existe tabela de advogados no banco; eles vêm das assinaturas das peças, e a ferramenta deduz o lado pela peça que só um lado apresenta." | 10 s |
| 3 | Clicar **Já foi julgado?** | "Sim": os três sinais conferem (data, movimentação, documento); a sentença foi lida; decisão parcialmente procedente, R$ 1.523,18 | "Em 4.426 processos há data de sentença sem o texto. Por isso o código cruza três sinais e o modelo só repete o resultado." | 7 s |
| 4 | Clicar **Minuta de sentença** | Primeira linha "PROPOSTA DE MINUTA — texto não proferido"; RELATÓRIO, FUNDAMENTAÇÃO, DISPOSITIVO; nos passos, `prepare_draft` e as cinco peças lidas, **sem** a sentença existente | "O aviso é garantido por código, não pelo modelo. A sentença que já existe fica fora da leitura: a minuta é uma proposta a partir das peças, não uma cópia." | 12 s |

### Bloco 2 — as mesmas 4 perguntas no processo 1 (zero documentos) — 31 s de modelo

Colar as perguntas trocando o número por `0000001-43.2021.8.99.9014` (ficam prontas no fim deste arquivo).

| # | O que mostrar | O que dizer | Tempo |
|---|---|---|---:|
| 5 | Resumo só pelo andamento; "não constam documentos"; o aviso de apelação depois do trânsito em julgado | "63% dos processos do banco não têm nenhuma peça. Ele resume pelo andamento e diz isso, em vez de inventar fatos a partir do assunto." | 12 s |
| 6 | Partes e juiz certos; advogados e pedidos: "não consta no banco" | "Sem documentos não há advogados nem pedidos; a resposta certa é dizer que não consta." | 8 s |
| 7 | "Sinais divergentes": data e movimentação presentes, documento ausente; decisão e fundamentos: não consta | "Houve sentença, mas o texto não está no banco. Ele separa 'foi julgado' de 'o que decidiu'." | 4 s |
| 8 | Recusa da minuta: faltam a petição inicial e a contestação | "Recusar com motivo é uma resposta correta." | 7 s |

### Bloco 3 — a pergunta que falha de propósito (D82) — 21 s de modelo

Colar: **Com uma única consulta SQL, conte quantos documentos mencionam no texto o nome de alguma parte de um processo diferente do seu.**

Abrir os três passos: a primeira consulta interrompida por passar de 5 segundos; a segunda falha (de novo o tempo, ou uma tabela que não existe); a terceira nem executa, com a mensagem de limite de tentativas. A resposta admite que não foi possível e diz por quê.

Dizer: "É a resposta à pergunta 'o que acontece quando ele erra': o SQL livre só lê, tem limite de linhas, de tempo e de tentativas; o erro volta para o modelo como observação, e depois de duas falhas ele é obrigado a parar e admitir."

### Bloco 4 — "Ver consumo" (sem modelo)

Clicar **Ver consumo** embaixo da última resposta. Mostrar: total da demonstração (9 respostas, cerca de R$ 1,40), a tabela por tipo de pergunta, os três gráficos e a projeção mensal com o ponto de equilíbrio do servidor próprio.

Dizer: "O custo por pergunta quase não depende do tamanho da base, porque as ferramentas devolvem só o necessário; o que cresce é o volume. A partir de ~145 mil respostas por mês, um servidor próprio com modelo aberto sai mais barato e os dados não saem do tribunal."

### Bloco 5 — o mesmo agente com o modelo local — 62 s de modelo

1. **Novo chat** (botão no topo; confirmar). Na engrenagem, escolher `ollama:qwen3:4b-instruct-2507-q4_K_M`.
2. Colar: **Quem é o juiz do processo 0000007-79.2023.8.99.9014?** — 54 s. Enquanto espera, dizer: "É o mesmo código, com um modelo de 4 bilhões de parâmetros rodando neste notebook de 8 GB: nada sai da máquina. Ele é 10 a 40 vezes mais lento na escrita, por isso a demonstração usa o modelo pago; a troca é uma linha de configuração."
3. Na engrenagem, voltar para o Gemini. Colar: **E quem são as partes?** — 8 s. Mostrar que a conversa e o processo em foco continuaram depois da troca.

Não pedir resumo nem minuta ao modelo local ao vivo: 3 a 4 minutos cada (D78), e a minuta dele sai contraditória (D60).

### Fechamento

Voltar ao `DECISOES.md` no navegador ou no editor se a banca perguntar por uma decisão; as respostas da arguição estão em `docs/arguicao.md` (T12.6).

## Plano B

| Se… | Então… |
|---|---|
| O Gemini responder com "serviço indisponível" (erro 503 ou 429) | O chat avisa e tenta de novo sozinho em 5 s e 10 s (D41). Se a terceira tentativa falhar, trocar para o modelo local na engrenagem, **no mesmo chat**, e seguir só com perguntas curtas (juiz, partes, valor da causa, "já foi julgado?" do processo 1). |
| A internet cair | Só o modelo local. Fazer o bloco 5 e as perguntas curtas acima; se sobrar tempo, o resumo do processo 1 (80 s, D53). Pergunta que falha no local: "Usando uma consulta SQL, calcule o percentil 90 do valor da causa por classe processual" — ele erra a função, lê o erro e admite (D52, D82). |
| O navegador ou o Chainlit travar | Terminal: `uv run case-assistant`, mesmas perguntas; cada ferramenta aparece como `→ find_case(...)`. O modelo é o `LLM_MODEL` do `.env`. |
| A máquina ficar lenta (pressão de memória amarela ou vermelha) | Fechar o que estiver aberto além do Safari e do terminal; o modelo local só entra no bloco 5. |
| O Gemini inventar uma citação com nome de ferramenta ou sugerir outro processo (visto na bateria de 29/09, D76) | Apontar na tela: a citação não corresponde a nenhum passo, e é exatamente o tipo de erro que a fundamentação visível deixa conferir. |

## Perguntas prontas para colar

```text
Resuma o processo 0000001-43.2021.8.99.9014, destacando os principais fatos e o andamento processual.
Quem são as partes, o magistrado e os advogados do processo 0000001-43.2021.8.99.9014? Quais são os pedidos apresentados?
O processo 0000001-43.2021.8.99.9014 já foi julgado? Se sim, qual foi a decisão e quais foram seus fundamentos?
Elabore uma minuta de sentença para o processo 0000001-43.2021.8.99.9014, com base nos fatos e documentos disponíveis.
Com uma única consulta SQL, conte quantos documentos mencionam no texto o nome de alguma parte de um processo diferente do seu.
Quem é o juiz do processo 0000007-79.2023.8.99.9014?
E quem são as partes?
```

## Ensaio de 29/09/2026

Uma sessão, histórico contínuo, Gemini nas perguntas 1 a 8 e 10; ferramentas, pedidos ao modelo, tempo e custo de cada resposta:

| # | Pergunta | Ferramentas | Pedidos | Tempo | Custo |
|---|---|---|---:|---:|---:|
| 1 | Resumo do 3161 | find_case, list_movements, list_documents, list_parties, read_document ×3 | 8 | 19 s | R$ 0,22 |
| 2 | Partes, juiz e advogados do 3161 | find_case, list_parties, list_documents | 4 | 10 s | R$ 0,19 |
| 3 | Já foi julgado? (3161) | find_case, read_document | 3 | 7 s | R$ 0,17 |
| 4 | Minuta do 3161 | prepare_draft, read_document ×5 | 5 | 12 s | R$ 0,26 |
| 5 | Resumo do processo 1 | find_case, list_movements, list_documents, list_parties | 5 | 12 s | R$ 0,18 |
| 6 | Partes, juiz e advogados do processo 1 | list_parties, find_case, list_documents | 4 | 8 s | R$ 0,18 |
| 7 | Já foi julgado? (processo 1) | find_case | 2 | 4 s | R$ 0,04 |
| 8 | Minuta do processo 1 (recusa) | prepare_draft | 2 | 7 s | R$ 0,04 |
| 10 | Pergunta que falha | run_sql ×3 | 4 | 21 s | R$ 0,09 |

Bloco 5 ensaiado à parte, numa conversa nova: local 54 s (`find_case`, 7,2 mil tokens de entrada), Gemini 8 s (`list_parties`). O custo por resposta é maior do que a média da bateria (R$ 0,05, D76) porque numa conversa só o histórico acumula: da pergunta 2 em diante, cada pedido leva de 24 a 40 mil tokens.

**Erro de roteiro corrigido no ensaio:** a primeira versão trocava para o modelo local no fim, com o histórico de 8 respostas; "E quem é o juiz?" levou 209 s, porque o modelo local teve de reler tudo. A troca vai para uma conversa nova.
