# E14 — Melhorias de uso

[← Roadmap](../ROADMAP.md)

**Resultado do épico:** melhorias que aparecem com o uso frequente da aplicação, cada uma como tarefa pequena, entregue pelo mesmo fluxo de branch e PR. É um épico contínuo: novas tarefas entram à medida que forem encontradas (D83).
**Por que um épico próprio:** os épicos anteriores fecham com o entregável; o uso do dia a dia levanta ajustes de tela, instalação e conforto que não cabem em nenhum deles.

---

### T14.1 — Identidade visual do chat: imagem do TJSC, subtítulo e crédito `[x]`
- **Objetivo:** a tela do chat mostra a imagem do TJSC no lugar do logotipo do Chainlit, um subtítulo "Desafio técnico: Agente de IA para análise de processos" abaixo dela e, no rodapé da tela inicial, abaixo das quatro perguntas, o crédito "Desenvolvido por André Piacentini em setembro de 2026", com links para o site do autor (<https://andrepiacentini.com.br>) e o LinkedIn (<https://www.linkedin.com/in/andrepiacentini/>).
- **Passos:** a imagem do TJSC é a da página do desafio, <https://desafio-ia.sandbox.tjsc.jus.br/assets/logo.png> (baixar e versionar em `public/`; se só houver uma versão, usá-la nos dois temas e conferir a legibilidade no escuro); criar a pasta `public/` com `logo_light.png`, `logo_dark.png` e o favicon, que o Chainlit serve sozinho; conferir na documentação do Chainlit 2.12 onde entram o subtítulo e o rodapé — `description` no `config.toml`, a tradução da marca d'água (`pt-BR.json`) ou `custom_css`/`custom_js` em `public/` — e escolher o caminho com menos código; versionar os arquivos novos (o `.gitignore` já mantém `config.toml` e a tradução); testar no Safari com tema claro e escuro; registrar a decisão.
- **Pronto quando:** a tela inicial mostra imagem, subtítulo e crédito com os links funcionando, nos dois temas, e a tela de conversa mostra a imagem no lugar do logotipo.
- **Depende de:** E10.

### T14.2 — README: instalação no Windows e no Linux `[ ]`
- **Objetivo:** o `README.md` explica a instalação e a execução também no Windows e nas principais distribuições Linux, com o mesmo passo a passo do macOS.
- **Passos:** Windows: `uv` pelo instalador oficial (PowerShell), Ollama para Windows, `.env` e comandos no PowerShell, as variáveis do servidor Ollama (`OLLAMA_CONTEXT_LENGTH`, `OLLAMA_KV_CACHE_TYPE`) como variáveis de ambiente do usuário; Linux: `uv` pelo instalador oficial, Ollama pelo script oficial, variáveis no serviço do `systemd` (`systemctl edit ollama`), cobrindo Ubuntu/Debian e Fedora; mencionar o WSL como alternativa no Windows; testar o caminho Linux num contêiner Ubuntu (instalação, `uv sync`, `pytest`); o Windows fica marcado como não testado, a menos que haja uma máquina disponível; a seção do Ollama no README perde a frase "não foi testado neste projeto" no que for testado.
- **Pronto quando:** o README tem uma subseção por sistema, o caminho Linux foi seguido num ambiente limpo e o que não foi testado está dito.
- **Depende de:** T12.1, T12.2.
