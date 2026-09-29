# E11 — Ajuste do modelo local

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** tempo e memória do modelo local medidos no MacBook M1 de 8 GB, para ele servir de plano B da demonstração e de base de comparação com o modelo pago.
**Por que depois da bateria de avaliação:** cada ajuste é medido pela bateria (E09) — acelerar não pode custar acerto.
**Escopo revisto (D71):** a demonstração usa o Gemini; o local fica a um clique no seletor da tela. Ficam as tarefas que medem (T11.1, T11.3 e a opcional T11.6); saem as que tentariam tornar o local o principal (T11.4, T11.5).

---

### T11.1 — Tamanho da memória de conversa do modelo `[x]`
- **Objetivo:** configurar a janela de contexto em 16 mil tokens e a compactação da memória do modelo (`q8_0`).
- **Passos:** configurar `num_ctx` e `OLLAMA_KV_CACHE_TYPE=q8_0`; medir uso de RAM com o Monitor de Atividade. Urgência medida na T5.6 (D40): o Ollama está em 4.096 tokens e instruções + ferramentas já ocupam ~2.900 — um resumo com documentos lidos estouraria sem aviso. Verificar se o prefixo `ollama:` do Pydantic AI repassa `num_ctx` ou se é preciso configurar no servidor (`OLLAMA_CONTEXT_LENGTH`).
- **Pronto quando:** o uso total fica abaixo de ~7 GB durante a pergunta de resumo.
- **Depende de:** E05.
- **Para explicar à banca:** "Calculei o orçamento de memória antes: modelo, contexto e sistema cabem em 7 dos 8 GB."

### T11.2 — Desligar o "modo raciocínio" `[-]`
- **Cancelada (D25):** o modelo padrão passou a ser a variante *instruct*, que não tem modo raciocínio; não há o que desligar. A variante com raciocínio ignora `think=False`.
- **Objetivo:** desativar o raciocínio interno do Qwen3 para respostas mais rápidas.
- **Passos:** configurar `think=False`; comparar tempo e placar antes e depois.
- **Pronto quando:** a comparação está anotada no `DECISOES.md`.
- **Depende de:** E09.
- **Para explicar à banca:** "O raciocínio interno deixava cada resposta mais lenta sem melhorar o uso das ferramentas."

### T11.3 — Medir o tempo das 4 perguntas do edital `[x]`
- **Objetivo:** tabela de tempo por pergunta no modelo local, com tokens por segundo.
- **Passos:** rodar as 4 perguntas no 3161; cronometrar; registrar os tokens de entrada e de saída (registro da T13.1) e calcular tokens por segundo, separando a leitura do prompt da geração da resposta — a suspeita é que a demora vem mais da leitura das instruções e dos documentos do que da escrita.
- **Pronto quando:** a tabela está no `DECISOES.md`.
- **Depende de:** T11.1, T11.2.
- **Para explicar à banca:** "Sei quanto cada pergunta demora e escolhi o modelo da demo com base nisso."

### T11.4 — Enxugar as respostas das ferramentas `[-]`
- **Cancelada (D71):** o modelo local deixou de ser o da demonstração. As falhas dele na bateria (D65) e na minuta (D60) são de raciocínio, não de tamanho da resposta das ferramentas; as movimentações já foram enxugadas na D53.
- **Objetivo:** reduzir o volume de dados que as ferramentas devolvem, se a T11.3 mostrar lentidão.
- **Passos:** identificar a ferramenta com resposta maior; remover campos não usados; medir de novo. Pista da T5.4: instruções + descrições das 9 ferramentas somam ~2.900 tokens de entrada, e a 1ª pergunta da sessão leva 19–27 s (as seguintes, 1–2 s) — enxugar as descrições e/ou "aquecer" o modelo ao abrir a sessão.
- **Pronto quando:** o tempo melhorou sem piorar o placar do E09 (ou a tarefa é cancelada por não ser necessária).
- **Depende de:** T11.3.
- **Para explicar à banca:** "Menos texto enviado ao modelo significa resposta mais rápida."

### T11.5 — Avaliar o modelo reserva na bateria `[-]`
- **Cancelada (D71):** com o Gemini como principal e o `qwen3:4b` como plano B, um terceiro modelo, menor e pior em redação (D26), não muda a decisão.
- **Objetivo:** saber se o `qwen3:1.7b` ainda acerta o suficiente para ser o plano B da apresentação.
- **Já feito na T1.8 (D26):** download, confirmação de que `think=false` funciona nele, medição de velocidade e memória.
- **Passos:** rodar a bateria (E09) com o 1.7b; comparar o placar com o do modelo padrão.
- **Pronto quando:** o placar está registrado e há decisão sobre levá-lo para a demo.
- **Depende de:** E09.
- **Para explicar à banca:** "Tenho um modelo menor testado para o caso de a máquina ficar sem memória ao vivo."

### T11.6 — Medir a memória com videochamada aberta (opcional) `[-]`
- **Cancelada (D78):** a apresentação continua presencial (D28), regra desta tarefa; o pico de memória do modelo já está medido na D77.
- **Opcional (D28):** o edital prevê apresentação **presencial**. Esta tarefa só é feita se a apresentação passar a ser remota; caso contrário, é cancelada no fim do E11.
- **Objetivo:** saber se a demo com modelo local aguenta o cenário real: Chainlit no navegador **e** uma videochamada aberta ao mesmo tempo.
- **Passos:** fechar todos os outros programas; abrir o Chainlit **sempre no Safari**, só com essa aba; abrir uma chamada do Google Meet em **outro navegador** (Chrome), com câmera e compartilhamento de tela ativos; rodar as 4 perguntas do edital no processo 3161 e a minuta; acompanhar a "Pressão de memória" e o uso de swap no Monitor de Atividade; anotar o tempo de cada resposta. Repetir com o `qwen3:1.7b` se a pressão ficar amarela ou vermelha.
- **Pronto quando:** o `DECISOES.md` registra a cor da pressão de memória, o swap usado e os tempos, e a decisão de qual modelo levar para a demo (local 4B, local 1.7B ou nuvem).
- **Depende de:** T11.1 e E10.
- **Para explicar à banca:** "Não confiei só na conta: testei a demonstração com a videochamada aberta, que seria o cenário real de uma apresentação remota, e escolhi o modelo com base na medição."
