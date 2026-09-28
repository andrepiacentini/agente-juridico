# Roteiro — troca de processo no meio da conversa (T6.4)

Testa se o agente troca de processo quando um novo número aparece, se continua no processo novo nas perguntas sem número e se volta ao primeiro sem misturar os dados. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D46.

Todas as perguntas vão numa única conversa, nesta ordem. O esperado foi conferido no banco.

| # | Pergunta | Processo em foco depois | Deve conter | Não deve conter |
|---|---|---|---|---|
| 1 | Qual o assunto do processo 0000007-79.2023.8.99.9014? | 0000007-79.2023.8.99.9014 | Acidente de Trânsito | |
| 2 | Quem é o juiz? | 0000007-79.2023.8.99.9014 | Luiz Bonetti Vasconcelos; aviso de juiz aposentado | Pedro Cunha Nichele |
| 3 | E o processo 0000001-43.2021.8.99.9014, qual o assunto? | 0000001-43.2021.8.99.9014 | Rescisão Contratual c/c Perdas e Danos | Acidente de Trânsito |
| 4 | e as partes? | 0000001-43.2021.8.99.9014 | Carlos Bertoldi Boeing e Pedro Vieceli (polo ativo); Banco Meridional S.A. (polo passivo) | João Ziegler Rocha; Operadora de Saúde Cambirela; "advogado" como rótulo das partes |
| 5 | qual o valor da causa? | 0000001-43.2021.8.99.9014 | R$ 21.495,98 | R$ 3.796,73 |
| 6 | Voltando ao 0000007-79.2023.8.99.9014: quem são as partes? | 0000007-79.2023.8.99.9014 | João Ziegler Rocha (autor); Operadora de Saúde Cambirela Ltda (réu) | Carlos Bertoldi Boeing; Banco Meridional |

## Resultado — 27/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

Foram 2 rodadas. Nas duas, o foco e os dados de todas as respostas estavam certos.

- **Ferramentas:** o modelo chamou `find_case` nos turnos 1 e 3 e `list_parties` nos turnos 4 e 6, sempre com o número certo. Nos turnos 2 e 5, respondeu pelo histórico, sem chamar ferramenta.
- **Tempo:** 10 a 43 s por pergunta.
- **Erro do modelo (rodada 2, turno 4):** rotulou os autores como "Autores (advogados)". São partes, não advogados.
- **Aviso fora de lugar (rodada 1, turno 4):** o modelo repetiu, na resposta sobre as partes, o aviso de juiz aposentado que veio do `find_case` do turno 3. O aviso é verdadeiro (Pedro Cunha Nichele está aposentado), mas não foi perguntado.
- **Citação:** nenhuma resposta cita a fonte no formato combinado; em vez disso aparece "[warning]". Isso fica para a T7.7.
