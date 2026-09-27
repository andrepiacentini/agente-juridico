"""Instruções do agente (system prompt): papel, regras de fundamentação e processo em foco (E05, E07)."""

# Mapa do banco para a consulta livre (run_sql). As armadilhas foram medidas no banco real (DECISOES.md D13, D34–D38);
# os testes conferem que toda coluna aparece aqui e que os exemplos rodam.
DATABASE_DESCRIPTION = """\
Banco SQLite de processos judiciais fictícios, somente leitura. Prefira as ferramentas prontas; use SQL só para o que elas não cobrem. O resultado vem limitado a 50 linhas.

Tabelas (colunas):
- processo(id, numero, classe, assunto, comarca, unidade_id, magistrado_id, dt_aut, data_sentenca, valor_causa, situacao): 10.000 processos; numero no padrão CNJ 0000007-79.2023.8.99.9014; dt_aut = data de autuação.
- unidade(id, comarca, vara, dt_ini, status): varas; status 'ativa' ou 'desativada'.
- magistrado(id, nome, unidade_id, data_inicio, situacao): juízes; situacao 'ativo', 'aposentado' ou 'removido'.
- parte(id, nome, tipo, documento, data_cadastro): pessoas; documento = CPF ou CNPJ.
- processo_parte(id, processo_id, parte_id, polo): liga partes a processos; polo 'ativo' (autor) ou 'passivo' (réu).
- movimentacao(id, processo_id, codigo, descricao, data_mov): andamento processual.
- documento(id, processo_id, tipo, autor, dt_juntada, num_paginas, texto): peças; texto é longo.

Armadilhas:
- Datas são texto AAAA-MM-DD: compare como texto (dt_aut >= '2024-01-01').
- situacao do processo tem maiúsculas misturadas: use LOWER(TRIM(situacao)) = 'julgado'.
- 1.044 processos não têm magistrado: use LEFT JOIN magistrado, senão eles somem.
- Julgamento nunca vem de um sinal só: cruze data_sentenca, movimentacao.codigo IN (9219, 9220, 9221) e documento.tipo IN ('Sentença', 'Sentença Homologatória de Acordo').
- Comarca e nomes têm grafias diferentes (acento, espaço, caixa, "S. José"): compare com comparable_district(comarca) e comparable_text(coluna), que tiram acento e caixa.
- O papel da parte no processo é processo_parte.polo; parte.tipo é do cadastro e não serve para isso.
- Nomes de parte se repetem: identifique pessoas por parte.documento, não pelo nome.
- Advogados não têm tabela: estão em documento.autor, no formato 'Dr. Fulano — OAB/SC 99.170'.
- 402 movimentações não pertencem a nenhum processo: faça JOIN processo quando contar andamentos.
- valor_causa pode ser nulo, zero ou 9999999999 (valor de preenchimento).
- Não selecione documento.texto em listas; para ler um documento use a ferramenta read_document.

Exemplo: SELECT m.nome, COUNT(*) AS processos FROM processo p LEFT JOIN magistrado m ON m.id = p.magistrado_id WHERE LOWER(TRIM(p.situacao)) = 'julgado' GROUP BY m.id ORDER BY processos DESC
Exemplo: SELECT u.vara, COUNT(*) AS processos FROM processo p JOIN unidade u ON u.id = p.unidade_id WHERE comparable_district(p.comarca) = 'sao jose' GROUP BY u.vara
"""
