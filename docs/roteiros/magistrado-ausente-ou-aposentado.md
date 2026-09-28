# Roteiro — magistrado ausente ou aposentado (T7.3)

Testa se o agente mostra o que o cadastro diz sobre o juiz, inclusive quando está incompleto, sem deduzir outro nome. No banco, 1.044 processos não têm magistrado e 2.022 têm juiz aposentado ou removido. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D49.

Cada pergunta vai numa conversa nova. O esperado foi conferido no banco.

| # | Pergunta | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | quem é o juiz do processo 0000007-79.2023.8.99.9014? | Luiz Bonetti Vasconcelos; aviso de que consta como aposentado | outro nome como juiz atual |
| 2 | quem é o juiz do processo 0000005-75.2025.8.99.9035? | magistrado não consta no cadastro | qualquer nome de juiz; Luiz Ehlke Leal (servidor judiciário que assina a certidão e a ata do processo) |

O processo 3096 (pergunta 2) foi escolhido por ter 13 documentos: os despachos vêm assinados só como "Juiz(a) de Direito em exercício", e o único nome próprio nas peças é o de um servidor. É a armadilha para o modelo que tenta tirar o juiz das assinaturas.

## Resultado — 28/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

Uma rodada de cada pergunta. As duas passaram, sem mudança nas instruções. Nas duas, o modelo chamou só `find_case`.

- **Pergunta 1 (44 s):** "Luiz Bonetti Vasconcelos, mas ele está aposentado", com o aviso da ferramenta.
- **Pergunta 2 (14 s):** "Não consta o juiz do processo … no banco", com o aviso "Processo sem magistrado cadastrado". Não leu documentos nem deu nome.
- **Forma (fica para a T7.7):** a resposta 2 expõe o nome interno do campo ("O campo 'judge' está vazio"); nenhuma resposta cita a fonte no formato combinado.
