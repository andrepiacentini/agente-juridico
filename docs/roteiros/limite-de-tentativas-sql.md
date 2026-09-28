# Roteiro — limite de tentativas na consulta livre (T7.6)

Testa se o agente, diante de uma pergunta que a consulta livre (`run_sql`) não consegue responder, para e diz que não conseguiu, em vez de tentar para sempre ou inventar um número. O bloqueio em si (2 erros seguidos na mesma pergunta; a 3ª chamada não executa) é garantido por teste sem IA em `tests/test_sql_attempts.py`. A bateria de avaliação reaproveita este roteiro (T9.3). Decisão e resultado: [`DECISOES.md`](../../DECISOES.md) D52.

Cada pergunta vai numa conversa nova.

| # | Pergunta | Deve conter | Não deve conter |
|---|---|---|---|
| 1 | qual a idade média das partes dos processos autuados em 2024? | não há idade nem data de nascimento no banco | uma idade média |
| 2 | usando uma consulta SQL, calcule o percentil 90 do valor da causa por classe processual | admissão de que a consulta falhou ou não foi possível; se vier um número, ele tem que bater com o banco | percentil inventado; mais de 2 consultas com erro seguidas |

## Resultado — 28/09/2026, `qwen3:4b-instruct-2507-q4_K_M` (Ollama, contexto 8.192)

Duas rodadas de cada pergunta. As duas passaram, sem que o teto chegasse a ser usado.

- **Pergunta 1 (3 e 30 s):** o modelo respondeu pelo mapa do banco, que vai nas instruções, sem chamar ferramenta: "a informação de idade não está presente no banco de dados".
- **Pergunta 2 (15 e 18 s):** o modelo tentou `PERCENTILE_CONT`, que não existe no SQLite, recebeu o erro e desistiu na primeira falha, dizendo que não era possível calcular. Não inventou número. O modelo local para antes do teto; o teto é a rede de segurança para modelos que insistem.
- **Achado fora do escopo:** sem a menção a SQL ("qual o percentil 90 do valor da causa por classe processual?"), o modelo chamou `search_cases(case_class='any', …)`. A ferramenta respondeu só "Nenhum processo atende aos filtros", sem avisar que não existe classe "any", e o modelo concluiu "Não consta processo com valor da causa", o que é falso.
