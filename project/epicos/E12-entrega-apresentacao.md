# E12 — Entrega e apresentação

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** os 4 entregáveis do edital prontos (código, README, registro de decisões, demonstração) e o material para a arguição.

---

### T12.1 — Escrever o `README.md` `[x]`
- **Objetivo:** instruções para instalar e rodar do zero.
- **Passos:** pré-requisitos (uv, Ollama); `uv sync`; `ollama pull`; configurar `.env`; rodar terminal e web; rodar testes; mapa das pastas.
- **Pronto quando:** o README cobre todos os comandos na ordem.
- **Depende de:** E05 (E10 se feito).
- **Para explicar à banca:** "O README foi escrito para quem nunca viu o projeto."

### T12.2 — Teste de instalação do zero `[x]`
- **Objetivo:** confirmar que alguém sem contexto sobe o projeto em 5 minutos.
- **Passos:** clonar o repositório em outra pasta; seguir só o README; anotar cada tropeço e corrigir o README.
- **Pronto quando:** a instalação funciona seguindo apenas o README.
- **Depende de:** T12.1.
- **Para explicar à banca:** "Testei o README como se fosse outra pessoa, num clone limpo."

### T12.3 — Revisar o `DECISOES.md` `[x]`
- **Objetivo:** conferir se toda decisão tem justificativa e se os termos técnicos estão no glossário.
- **Passos:** reler; completar lacunas; conferir links do glossário.
- **Pronto quando:** nenhuma decisão sem "por quê" e nenhum termo técnico sem explicação.
- **Depende de:** todos os épicos anteriores.
- **Para explicar à banca:** "O registro foi escrito ao longo do projeto, não no final — aqui só revisei."

### T12.4 — Roteiro da demonstração `[x]`
- **Objetivo:** sequência de perguntas da demo, com tempo estimado e plano B.
- **Passos:** ordem: 4 perguntas no 3161 → mesmas no processo 1 → troca de modelo → pergunta que falha (T12.5); plano B: terminal + Claude.
- **Pronto quando:** o roteiro está em `docs/roteiro-demo.md` e foi ensaiado uma vez cronometrado.
- **Depende de:** E09.
- **Para explicar à banca:** (é o próprio roteiro).

### T12.5 — Pergunta que falha de propósito `[x]`
- **Objetivo:** escolher uma pergunta que mostre o agente errando uma consulta, lendo o erro e se recuperando (ou admitindo o limite).
- **Passos:** testar candidatas com `consultar_sql`; escolher a que se comporta de forma previsível.
- **Pronto quando:** a pergunta está no roteiro e se comporta igual em 3 execuções.
- **Depende de:** E04, T7.6.
- **Para explicar à banca:** responde diretamente à arguição 2 — "o que acontece quando ele erra?".

### T12.6 — Respostas para as 5 perguntas da arguição `[ ]`
- **Objetivo:** texto curto para cada pergunta, com links para o `DECISOES.md`.
- **Passos:** partir do `plan.md` §8; atualizar com o que realmente aconteceu; salvar em `docs/arguicao.md`.
- **Pronto quando:** as 5 respostas cabem em uma página e cada uma aponta uma evidência no projeto.
- **Depende de:** T12.3.
- **Para explicar à banca:** (é o próprio material).

### T12.7 — Conceder acesso ao repositório `[ ]`
- **Objetivo:** dar acesso aos e-mails indicados no convite.
- **Passos:** publicar o repositório (privado); adicionar os e-mails; confirmar que o último commit está no servidor.
- **Pronto quando:** convites enviados e confirmados.
- **Depende de:** T12.1 a T12.3.
- **Para explicar à banca:** —
