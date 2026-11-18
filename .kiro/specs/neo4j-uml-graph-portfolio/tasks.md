# Implementation Plan: neo4j-uml-graph-portfolio

## Overview

Este plano cria, do zero, o repositório de portfólio que modela um diagrama de classes UML de e-commerce como grafo no Neo4j 5.x (sem APOC). Verificação feita no disco: existem apenas as pastas vazias `cypher/`, `data/` e `docs/images/`. O arquivo `data/classifiers.csv` **não existe**, ao contrário do que o `requirements.md` afirma (ponto 3 do design). Todos os artefatos abaixo precisam ser criados.

Decisões do plano:

- Linguagem dos testes: Python 3 (pytest, Hypothesis, driver `neo4j` e `testcontainers`), conforme o design. Scripts e dados são Cypher e CSV.
- Documentação em português do Brasil. Nenhum arquivo do projeto cita o termo proibido do Requirement 12.1. Os testes montam o padrão por concatenação de fragmentos.
- Tarefas marcadas com **[AÇÃO DO USUÁRIO]** dependem de instância real do Neo4j, do Arrows.app, de capturas de tela ou de decisão de publicação. O agente NÃO deve automatizá-las nem inventar seus resultados. Ele só prepara o que for texto e aguarda o retorno do Autor.
- Nenhuma tarefa executa `git`. A publicação é uma tarefa manual final que respeita a regra de proteção da `main`.
- Testes com banco usam o marcador `neo4j` e exigem Docker. Testes puros rodam com `pytest -m "not neo4j"`.
- O design resolve o ponto 1 adotando a numeração `01_constraints`, `02_load`, `03_queries`, `04_validate`, `99_reset`.

## Tasks

- [ ] 1. Preparar a base do repositório e o esqueleto de testes
  - [x] 1.1 Criar `.gitignore` e `LICENSE` na raiz
    - `.gitignore` com `.DS_Store`, `Thumbs.db`, `.idea/`, `.vscode/`, `.vs/`, `neo4j/data/`, `neo4j/logs/`, `neo4j/import/`, e também `__pycache__/`, `.pytest_cache/`, `.hypothesis/`, `.venv/`, `.env`
    - `LICENSE` com texto MIT completo, ano corrente e titular dos direitos autorais. Confirmar com o Autor o nome do titular antes de finalizar; usar `Gustavo Vianna` apenas como valor provisório
    - _Requirements: 1.3, 1.4, 12.5_

  - [x] 1.2 Criar o esqueleto da suíte de testes
    - `tests/requirements-dev.txt` com `pytest`, `hypothesis`, `neo4j` e `testcontainers`, versões fixadas
    - `pytest.ini` na raiz com os marcadores `neo4j` e `evidencias` e `testpaths = tests`
    - `tests/conftest.py` com a raiz do repositório e o caminho de `data/` e `cypher/` como fixtures, e perfil Hypothesis (`max_examples=100`, `deadline=None`)
    - `tests/helpers/__init__.py` vazio
    - _Requirements: 12.3_

- [x] 2. Criar o dataset e o validador de dataset
  - [x] 2.1 Criar `data/classifiers.csv`
    - Colunas `id`, `name`, `kind`, `isAbstract`, `package`, UTF-8, com cabeçalho
    - Exatamente 16 linhas conforme a tabela de pacotes do design: `domain` (7), `service` (4), `repository` (2), `infra` (3)
    - `kind` apenas `class`, `interface` ou `enum`. `Payment` com `isAbstract = true`. Contagem resultante: 12 `Class`, 3 `Interface`, 1 `Enum`
    - _Requirements: 5.1, 5.2_

  - [x] 2.2 Criar `data/relationships.csv`
    - Colunas `sourceId`, `targetId`, `type`, `role`, `multiplicity`
    - As 17 linhas da tabela de relacionamentos do design, incluindo `Payment -> StripeGateway` (violação `domain` para `infra`) e o ciclo `OrderService -> PaymentService -> NotificationService -> OrderService`
    - `role` e `multiplicity` preenchidos só em `ASSOCIATES`, `COMPOSED_OF` e `AGGREGATES`, em notação UML
    - Todos os `sourceId` e `targetId` existem em `classifiers.csv`
    - _Requirements: 5.3, 5.5, 5.6, 5.7, 5.8_

  - [x] 2.3 Criar `data/attributes.csv`, `data/methods.csv` e `data/calls.csv`
    - `attributes.csv`: `id`, `classifierId`, `name`, `dataType`, `visibility`, `isStatic`, `position`
    - `methods.csv`: `id`, `classifierId`, `name`, `returnType`, `visibility`, `isStatic`, `isAbstract`, `position`
    - `calls.csv`: `callerId`, `calleeId`, `sequence`
    - No máximo 200 linhas por arquivo e ao menos uma linha cada. Referências válidas. Ao menos uma cadeia de `CALLS` com 3 ou mais métodos, para dar sentido à Q07
    - Dados fictícios, sem nomes de pessoas, e-mails ou credenciais
    - _Requirements: 5.1, 5.3, 5.4, 5.9, 11.6_

  - [x] 2.4 Implementar o modelo de dataset e o validador
    - `tests/helpers/dataset_model.py`: estruturas em memória das cinco tabelas, leitura e escrita de CSV
    - `tests/helpers/validator.py`: `validate(dataset) -> list[Erro]`, cada erro com regra e número da linha. Regras: cabeçalhos, ao menos 1 linha, no máximo 200 linhas, `id` não vazio e único, referências resolvidas em relacionamentos, atributos, métodos e chamadas, `role` e `multiplicity` não vazios e casando com `^(\d+|\*)(\.\.(\d+|\*))?$` nos três tipos que exigem
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.8, 5.9_

  - [x] 2.5 Escrever o teste de propriedade do validador de dataset
    - Criar `tests/helpers/generators.py` com o gerador de dataset válido (2 a 12 classificadores, até 30 relacionamentos, ciclos e `EXTENDS` em cadeia) e as mutações inválidas (remover `id`, duplicar `id`, referência inexistente, `multiplicity` vazia, 201 linhas)
    - **Property 1: Validador de dataset aceita se, e somente se, as regras do Requirement 5 valem**
    - Comentário de etiqueta: `Feature: neo4j-uml-graph-portfolio, Property 1`
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.8, 5.9**

  - [x] 2.6 Escrever testes de exemplo do dataset real
    - Arquivo `tests/test_dataset_real.py`
    - Cinco arquivos presentes, UTF-8, validador sem erros, exatamente 16 classificadores
    - Ao menos um relacionamento de cada um dos seis tipos
    - Ao menos um ciclo de 2 a 5 classificadores distintos e `Payment -> StripeGateway` presente como a única dependência `domain` para `service`, `repository` ou `infra`
    - _Requirements: 5.1, 5.2, 5.5, 5.6, 5.7_

- [~] 3. Checkpoint - Dataset
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Criar os scripts Cypher de constraints, carga, validação e reset
  - [x] 4.1 Criar `cypher/01_constraints.cypher`
    - Quatro constraints nomeadas, todas com `IF NOT EXISTS`: `package_name_unique`, `classifier_id_unique`, `attribute_id_unique`, `method_id_unique`
    - Comentário de linha em português imediatamente antes de cada comando
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 4.2 Criar `cypher/02_load.cypher`
    - Quatorze instruções separadas por `;`, na ordem da tabela do design (4 blocos de nó, `CONTAINS`, `HAS_ATTRIBUTE`, `HAS_METHOD`, 6 tipos UML por filtro de `type`, `CALLS`), sem `CREATE` e sem `apoc.`
    - `LOAD CSV WITH HEADERS FROM 'file:///<arquivo>.csv'`, `WITH row WHERE row.id IS NOT NULL` nos nós, `MERGE` pelo identificador e `SET` para o restante
    - Conversão com `toBooleanOrNull` e `toIntegerOrNull`. Labels secundários `Class`, `Interface` e `Enum` por `FOREACH`/`CASE`
    - Relacionamentos com `MATCH` dos dois extremos antes do `MERGE`. `role`, `multiplicity` e `sequence` por `SET`
    - Comentário em português imediatamente antes de cada bloco, com arquivo lido, o que é criado e as conversões
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 12.3_

  - [x] 4.3 Criar `cypher/04_validate.cypher` e `cypher/99_reset.cypher`
    - `04_validate`: duas consultas somente leitura (contagem por label com `UNWIND labels(n)` e contagem por tipo de relacionamento)
    - `99_reset`: estágio 1 `DETACH DELETE` dos nós `Package`, `Classifier`, `Attribute` e `Method`; estágio 2 `DROP CONSTRAINT <nome> IF EXISTS` para as quatro constraints, separados por comentário
    - Comentários em português
    - _Requirements: 3.6, 7.9, 7.10_

  - [x] 4.4 Implementar o fixture de Neo4j e o oráculo de contagens
    - `tests/helpers/neo4j_fixture.py`: sobe um contêiner Neo4j 5.x Community sem APOC uma vez por sessão, grava CSVs na pasta `import`, divide cada script `.cypher` por `;` fora de comentários e literais e executa cada instrução em transação própria, expõe `reset()` que executa o `99_reset.cypher`, e ignora os testes com mensagem explícita se o Docker não estiver disponível
    - `tests/helpers/oracles.py`: contagens esperadas por label e por tipo de relacionamento a partir das linhas dos CSVs, e dump ordenado de nós e relacionamentos com propriedades
    - _Requirements: 3.5, 7.1, 7.5, 7.10_

  - [x] 4.5 Escrever o teste de propriedade da varredura de scripts
    - Arquivo `tests/test_scripts_text.py`
    - **Property 14: Scripts Cypher não usam APOC nem CREATE de dados**
    - Verificador de `apoc.` sem distinção de caixa em textos gerados, e varredura dos arquivos reais de `cypher/`. No `02_load.cypher`, sem comentários, sem `CREATE`. O `01_constraints.cypher` pode conter `CREATE CONSTRAINT`
    - **Validates: Requirements 7.2, 7.5, 12.3, 12.4**

  - [x] 4.6 Escrever o teste de propriedade das contagens após a carga
    - Arquivo `tests/test_load_counts.py`, marcador `neo4j`
    - **Property 2: Contagens após a carga são iguais às do oráculo**
    - Inclui a igualdade entre o resultado do `04_validate` e as contagens do oráculo
    - **Validates: Requirements 3.5, 5.2, 7.1, 7.5, 7.10**

  - [x] 4.7 Escrever o teste de propriedade da conversão de tipos
    - Arquivo `tests/test_load_types.py`, marcador `neo4j`. Estratégia de valores de coluna (`true`, `TRUE`, `1`, vazio, espaços, `1.5`, `abc`, números grandes e negativos) definida no próprio arquivo
    - **Property 3: Conversão de tipos nunca grava texto em propriedade booleana ou inteira**
    - **Validates: Requirements 7.3, 7.4**

  - [x] 4.8 Escrever o teste de propriedade de idempotência da carga
    - Arquivo `tests/test_load_idempotent.py`, marcador `neo4j`
    - **Property 4: A carga é idempotente**
    - **Validates: Requirements 7.7**

  - [x] 4.9 Escrever o teste de propriedade de retomada da carga
    - Arquivo `tests/test_load_resume.py`, marcador `neo4j`. Prefixo de 0 a 14 instruções executado antes da carga completa
    - **Property 5: Retomar uma carga interrompida converge para o mesmo grafo**
    - **Validates: Requirements 7.8**

  - [x] 4.10 Escrever o teste de propriedade de reset e recarga
    - Arquivo `tests/test_reset_reload.py`, marcador `neo4j`
    - **Property 6: Reset seguido de nova carga reproduz o estado**
    - **Validates: Requirements 7.9, 10.2**

  - [x] 4.11 Escrever testes de exemplo dos scripts de constraints e carga
    - Arquivo `tests/test_scripts_examples.py`, marcador `neo4j` onde precisar de banco
    - Exatamente 4 constraints, todas com `IF NOT EXISTS` e com comentário imediatamente antes
    - Duas execuções do `01_constraints` sem erro e com o mesmo catálogo
    - Duplicata de `id` rejeitada com preservação do nó original
    - Todo `LOAD CSV` precedido de comentário. Carga do dataset real em até 30 segundos
    - _Requirements: 5.10, 6.1, 6.2, 6.3, 6.4, 6.6, 7.6_

- [x] 5. Criar as consultas de negócio
  - [x] 5.1 Criar `cypher/03_queries.cypher`
    - `:param` no topo para `$nome`, `$interface`, `$metodo` e `$pacote`, sem valores literais fixos nas consultas
    - Oito consultas Q01 a Q08 da tabela do design, cada uma precedida de `// Qnn - <pergunta em português, até 200 caracteres>`
    - Q04 com a forma de ciclos do design (nós distintos e deduplicação pela rotação de menor `id`). Q06 com comentário que registra quais tipos de relacionamento entram no acoplamento. Sem `apoc.`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 12.3_

  - [x] 5.2 Implementar os oráculos das consultas e o extrator de consultas
    - Em `tests/helpers/oracles.py`: fechamento transitivo por busca em largura com limite opcional, ciclos simples de 2 a 5 nós normalizados pela rotação de menor `id`, filtro de violação de camadas, graus de entrada e saída com ordenação, implementadores concretos por `EXTENDS*0..`
    - Em `tests/helpers/neo4j_fixture.py`: função que extrai o texto de cada `Qnn` de `03_queries.cypher` e executa com parâmetros
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

  - [x] 5.3 Escrever o teste de propriedade de alcançabilidade
    - Arquivo `tests/test_queries_reach.py`, marcador `neo4j`
    - **Property 7: Consultas de alcançabilidade são iguais ao fechamento transitivo do oráculo**
    - Cobre Q01, Q03 e Q07, inclusive grafos com ciclos
    - **Validates: Requirements 9.2, 9.4, 9.8**

  - [x] 5.4 Escrever o teste de propriedade de detecção de ciclos
    - Arquivo `tests/test_queries_cycles.py`, marcador `neo4j`
    - **Property 8: Detecção de ciclos devolve cada ciclo simples uma única vez**
    - **Validates: Requirements 5.6, 9.5**

  - [x] 5.5 Escrever o teste de propriedade de violação de camadas
    - Arquivo `tests/test_queries_layers.py`, marcador `neo4j`
    - **Property 9: Violação de camadas é o filtro exato das dependências proibidas**
    - **Validates: Requirements 5.7, 9.6**

  - [x] 5.6 Escrever o teste de propriedade de implementadores concretos
    - Arquivo `tests/test_queries_implementers.py`, marcador `neo4j`
    - **Property 10: Implementadores concretos incluem herança e excluem abstratos e interfaces**
    - **Validates: Requirements 9.3**

  - [x] 5.7 Escrever o teste de propriedade de acoplamento
    - Arquivo `tests/test_queries_coupling.py`, marcador `neo4j`
    - **Property 11: Acoplamento é entrada, saída e total corretos, na ordem pedida**
    - **Validates: Requirements 9.7**

  - [x] 5.8 Escrever testes de exemplo das consultas no dataset real
    - Arquivo `tests/test_queries_examples.py`, marcador `neo4j`
    - Q04 devolve exatamente o ciclo `OrderService`, `PaymentService`, `NotificationService`. Q05 devolve exatamente `Payment -> StripeGateway` com pacote de destino `infra`. Q03 para `StripeGateway` alcança `Payment`, `PaymentService`, `NotificationService` e `OrderService`
    - Execução de cada consulta parametrizada sem o `:param` falha com erro de parâmetro ausente e deixa as contagens do grafo intactas
    - Nenhuma consulta contém valor literal fixo no lugar do parâmetro
    - _Requirements: 9.9, 9.11, 9.12_

- [~] 6. Checkpoint - Scripts e consultas
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Criar a documentação e os testes de conteúdo
  - [x] 7.1 Criar `docs/modelo-grafo.md`
    - Em português. Tabela de nós (labels base `Package`, `Classifier`, `Attribute`, `Method` e derivados `Class`, `Interface`, `Enum`) com propriedades, tipo de dado e identificador único
    - Tabela de relacionamentos (tipo, origem, destino, direção, propriedades ou "sem propriedades")
    - Mapeamento dos cinco conceitos UML (Classificador, Membro, Relacionamento_UML, Chamada, Pacote) e diagrama Mermaid do esquema
    - Registrar a distinção entre labels base e derivados (ponto 2 do design). Convenções: PascalCase, UPPER_SNAKE_CASE e camelCase
    - Referenciar as imagens de esquema apenas na tarefa 10.1, quando os arquivos existirem
    - _Requirements: 8.1, 8.2, 8.3, 8.7, 12.2_

  - [x] 7.2 Escrever o teste de propriedade do esquema documentado
    - Arquivo `tests/test_schema_doc.py`, marcador `neo4j`, com o parser de `docs/modelo-grafo.md`
    - **Property 12: O esquema observado está contido no Modelo_Grafo documentado**
    - Usa `db.schema.nodeTypeProperties()` e `db.schema.relTypeProperties()`
    - **Validates: Requirements 8.1, 8.2, 8.8**

  - [x] 7.3 Criar o `README.md` - apresentação, contexto, justificativa e domínio
    - Título, resumo, estrutura de pastas (`data/`, `cypher/`, `docs/images/`, com 1 a 2 frases cada)
    - Seção de contexto com 100 a 300 palavras, citando herança transitiva, análise de impacto e detecção de ciclos
    - Seção de justificativa comparando grafo e modelo relacional, com tabela cobrindo as três consultas, um exemplo Cypher de profundidade variável e o SQL equivalente com junções recursivas
    - Seção de domínio listando os quatro pacotes com 1 a 2 frases cada
    - Português do Brasil, sem o termo proibido
    - _Requirements: 1.5, 2.1, 2.2, 2.3, 2.4, 12.1, 12.2_

  - [x] 7.4 Ampliar o `README.md` - execução, contagens e perguntas de negócio
    - Pré-requisitos (Neo4j 5.0 ou superior na série 5.x, sem APOC, arquivos do dataset)
    - Passos numerados para Neo4j Desktop. Comando Docker único com portas HTTP e Bolt, credenciais de exemplo `<sua-senha>` com aviso de substituição e montagem de `data/` como `import`
    - Ordem de execução: `01_constraints`, `02_load`, `04_validate`, `03_queries`, e instrução de que a validação é somente leitura e roda logo após a carga (ponto 1 do design)
    - Tabela de contagens esperadas, calculada com o oráculo da tarefa 4.4 sobre os CSVs reais. Descrição do `99_reset` e o que fazer quando as contagens divergem ou o CSV não é encontrado
    - Tabela das oito perguntas com consulta, resultado esperado calculado pelo oráculo da tarefa 5.2 e coluna de evidência, que fica com o nome de arquivo previsto até a tarefa 10.1
    - Marcar no texto que os resultados esperados aguardam a confirmação do Autor na tarefa 9.1
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 7.10, 9.10, 12.6_

  - [x] 7.5 Ampliar o `README.md` - troubleshooting e espaço de validação
    - Seção com 5 a 15 problemas no formato Sintoma, Causa e Solução (a Solução com comando ou passo executável)
    - Os quatro obrigatórios: CSV fora da pasta `import`, booleano e numérico importados como texto, tipos de relacionamento dinâmicos sem APOC, nós duplicados por reexecução com `CREATE` (com consulta de contagem). Todos identificados como "problema potencial", pois ainda não foram observados
    - Seção "Validação" com campos pendentes para versão MAJOR.MINOR.PATCH, edição e data, claramente marcados como a preencher pelo Autor na tarefa 10.1. Não inventar valores
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 10.4_

  - [x] 7.6 Escrever o teste de propriedade de nomes e padrões
    - Arquivo `tests/test_names.py`
    - **Property 13: Nomes e identificadores seguem os padrões exigidos**
    - Validadores de nome de script, de nome de evidência e de caixa. Na pasta real `cypher/`, prefixos únicos. A checagem de um arquivo `qNN-*.png` por pergunta na pasta `docs/images/` usa o marcador `evidencias` e só roda na tarefa 10.2
    - **Validates: Requirements 1.2, 8.7, 11.1, 11.2**

  - [x] 7.7 Escrever o teste de propriedade do termo proibido
    - Arquivo `tests/test_forbidden_term.py`
    - **Property 15: Nenhum arquivo, nome ou metadado contém o termo proibido**
    - Padrão montado por concatenação de fragmentos. Varredura exclui `.git/` e `.kiro/`. Inclui texto de PNG, EXIF e XMP quando houver imagens
    - **Validates: Requirements 12.1**

  - [x] 7.8 Escrever o teste de propriedade dos links de imagem do README
    - Arquivo `tests/test_readme_links.py`
    - **Property 16: Todo link de imagem do README resolve para um arquivo existente**
    - Extrator de `![...](caminho)` que ignora blocos de código. Rejeita links absolutos e externos
    - **Validates: Requirements 8.6**

  - [x] 7.9 Escrever testes de exemplo do repositório e do README
    - Arquivo `tests/test_repo_smoke.py`
    - `README.md`, `LICENSE` não vazia com ano e titular, `.gitignore` com as entradas exigidas e pastas exigidas
    - Seções do README: contexto de 100 a 300 palavras, justificativa com blocos Cypher e SQL, todos os pacotes de `classifiers.csv` citados, passos de Desktop e Docker, ordem dos scripts, troubleshooting de 5 a 15 itens com rótulos corretos, e uma linha por pergunta na tabela de consultas
    - Varredura de padrões de segredo e verificação de que comandos com credencial usam `<sua-senha>`
    - Tabela de contagens do README igual ao oráculo do dataset real
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.4, 3.5, 4.1, 9.10, 12.5, 12.6_

- [~] 8. Checkpoint - Documentação e testes puros
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. **[AÇÃO DO USUÁRIO]** Validação em instância real e evidências visuais (não automatizar)
  - [x] 9.1 **[AÇÃO DO USUÁRIO]** Executar a sequência completa em uma instância real do Neo4j
    - Em Neo4j 5.x sem APOC, banco vazio, copiar `data/*.csv` para a pasta `import` e executar nesta ordem: `01_constraints`, `02_load`, `04_validate`, `03_queries`, `99_reset`. Cada script deve terminar com 0 erros
    - Depois do reset, rodar de novo `01_constraints`, `02_load` e `04_validate` e conferir resultados iguais aos da primeira vez
    - Conferir as contagens e os resultados esperados do README. Se algo divergir, corrigir dataset, script ou README e repetir a sequência inteira
    - Anotar a versão exata (MAJOR.MINOR.PATCH), a edição e a data
    - O agente não executa esta tarefa nem simula os resultados
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [~] 9.2 **[AÇÃO DO USUÁRIO]** Registrar os problemas realmente observados
    - Informar ao agente cada problema ocorrido na validação (sintoma, causa, solução, e para divergências: consulta, resultado obtido, esperado e correção)
    - Se nada ocorreu, informar isso, e o README permanece só com "problema potencial"
    - _Requirements: 4.6, 4.7, 10.3_

  - [~] 9.3 **[AÇÃO DO USUÁRIO]** Gerar a imagem de esquema do banco
    - Executar `CALL db.schema.visualization()` após a carga e salvar o PNG em `docs/images/schema-db.png`, mostrando todos os labels e tipos de relacionamento do `modelo-grafo.md`
    - _Requirements: 8.4_

  - [~] 9.4 **[AÇÃO DO USUÁRIO]** Desenhar o esquema no Arrows.app
    - Desenhar o esquema com as propriedades de cada label e de cada relacionamento, conforme `docs/modelo-grafo.md`
    - Exportar `docs/images/schema-arrows.png` e `docs/images/schema-arrows.json`
    - _Requirements: 8.5_

  - [~] 9.5 **[AÇÃO DO USUÁRIO]** Capturar as evidências visuais das oito perguntas
    - Um PNG por pergunta em `docs/images/`, nomeado `qNN-descricao-em-kebab-case.png` (por exemplo `q01-hierarquia-heranca.png`), com NN igual ao número da consulta
    - Cada imagem com largura mínima de 1200 px e no máximo 5 MB, mostrando o texto completo da consulta e o resultado, legível a 100% em tela de 1920 x 1080
    - Ao menos uma em modo grafo e ao menos uma em modo tabela
    - Sem nome de pessoa, e-mail, senha, token, endereço IP ou host de instância privada
    - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6_

  - [~] 9.6 **[AÇÃO DO USUÁRIO]** Revisar manualmente imagens e textos
    - Conferir legibilidade e ausência de dados sensíveis nas imagens (11.3, 11.5, 11.6) e o português do Brasil dos textos (12.2)
    - Registrar o resultado como lista de conferência no PR ou no repositório
    - _Requirements: 11.3, 11.5, 11.6, 12.2_

- [ ] 10. Integrar os resultados da validação manual
  - [~] 10.1 Atualizar README e `modelo-grafo.md` com os dados fornecidos pelo Autor
    - Pré-requisito: o Autor concluiu 9.1 a 9.5 e informou versão, edição, data, problemas observados e confirmação dos resultados esperados. Se faltar qualquer dado, perguntar ao Autor e não preencher por suposição
    - Preencher a seção "Validação" (versão MAJOR.MINOR.PATCH, edição, data)
    - Marcar como "observado" os problemas informados em 9.2 e manter os demais como "problema potencial"
    - Incluir as imagens de esquema no README e no `modelo-grafo.md` por link relativo para `docs/images/`
    - Inserir cada evidência imediatamente abaixo do título e do texto da pergunta, com texto alternativo de 10 a 150 caracteres que descreve a pergunta e o tipo de resultado (grafo ou tabela). Atualizar a coluna de evidência da tabela de perguntas
    - Remover o aviso de resultados pendentes do README
    - _Requirements: 4.6, 4.7, 8.4, 8.5, 8.6, 9.10, 10.4, 11.4_

  - [~] 10.2 Escrever e executar os testes das imagens e dos links reais
    - Arquivo `tests/test_images.py`, marcador `evidencias`
    - Assinatura PNG, largura mínima de 1200 px e no máximo 5 MB nas evidências, JSON do Arrows válido, nome no padrão `qNN-*.png`, exatamente um arquivo por pergunta do `03_queries.cypher`, ao menos uma imagem em modo grafo e uma em modo tabela registradas por lista no teste ou no README
    - Executar `pytest -m "not neo4j"` e `pytest -m evidencias`, incluindo links do README e varredura do termo proibido nos metadados das imagens
    - _Requirements: 8.6, 11.1, 11.2, 11.5, 11.7, 12.1_

- [~] 11. Checkpoint final - Ensure all tests pass, ask the user if questions arise.
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. **[AÇÃO DO USUÁRIO]** Publicação do repositório (sem executar git automaticamente)
  - [~] 12.1 **[AÇÃO DO USUÁRIO]** Publicar conforme o tipo de repositório
    - O agente NÃO executa `git add`, `commit`, `push`, `merge` ou qualquer comando git. Esta tarefa só orienta
    - Antes de publicar: confirmar que 9.1 terminou com 0 erros (Requirement 10.5), rodar uma ferramenta de varredura de segredos no histórico e nos arquivos (Requirement 12.5) e conferir que nenhum `.env` ou credencial será enviado
    - Caso A, repositório pessoal novo em `github.com/Gtvnv/*`: a regra permite commit e push direto na `main` enquanto o projeto for novo e pessoal. Mesmo assim, sem `push --force`, `reset --hard` ou reescrita de histórico, e com `git add` de arquivos específicos
    - Caso B, qualquer outro remoto (Azure DevOps, outras contas ou organizações, projetos de terceiros) ou repositório que não seja novo: nunca commitar na `main`. Criar uma branch como `feature/portfolio-neo4j-uml`, publicar com `git push -u origin <branch>` e abrir um Pull Request com título curto e descrição contendo resumo, o que foi testado (versão do Neo4j, data) e o que ficou pendente. O merge ocorre pelo PR, revisado por um humano
    - Se houver dúvida sobre o caso, tratar como Caso B
    - _Requirements: 10.5, 12.5_

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas em um MVP, mas as propriedades da suíte são a principal garantia de corretude dos scripts.
- O validador de dataset e as propriedades 1, 13 a 16 rodam sem banco. As propriedades 2 a 12 exigem Docker e o marcador `neo4j`.
- Tarefas **[AÇÃO DO USUÁRIO]** dependem de Neo4j real, Arrows.app, capturas de tela ou decisão de publicação. O agente deve aguardar o Autor e nunca fabricar versão, data, resultados ou imagens.
- A checagem de evidências por pergunta (Requirement 11.1) e a de links reais de imagem só passam depois da tarefa 10.1.
- O design deixa a numeração `01` a `04` com validação em 4º lugar no arquivo, mas a recomenda logo após a carga. Se o Autor preferir, ajustar o texto do Requirement 3.4 ou 1.2 no `requirements.md`.
- Pontos pendentes de decisão do Autor: titular da `LICENSE` e tipo de repositório de publicação.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "4.1", "4.3"] },
    { "id": 1, "tasks": ["2.1", "2.4", "4.2", "5.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.5", "4.4", "4.5", "7.1"] },
    { "id": 3, "tasks": ["2.6", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11", "5.2", "7.3"] },
    { "id": 4, "tasks": ["5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "7.2", "7.4", "7.6"] },
    { "id": 5, "tasks": ["7.5"] },
    { "id": 6, "tasks": ["7.7", "7.8", "7.9", "9.1", "9.4"] },
    { "id": 7, "tasks": ["9.2", "9.3", "9.5"] },
    { "id": 8, "tasks": ["9.6"] },
    { "id": 9, "tasks": ["10.1", "10.2"] },
    { "id": 10, "tasks": ["12.1"] }
  ]
}
```
