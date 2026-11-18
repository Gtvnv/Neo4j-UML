# Requirements Document

## Introduction

Este documento define os requisitos de um repositório de portfólio, de nível profissional, que demonstra a modelagem de diagramas de classes UML como um banco de dados em grafo no Neo4j 5.x. O domínio de exemplo é um sistema de e-commerce (clientes, pedidos, produtos, pagamentos, serviços, repositórios e componentes de infraestrutura).

O repositório deve permitir que um avaliador técnico entenda o problema, reproduza a carga do grafo em uma instância local do Neo4j, execute as consultas de negócio e confira as evidências visuais dos resultados.

Estado atual considerado: o workspace `c:\Develompment\WS-Personal\Neo4j_UML` contém as pastas `cypher/`, `data/` e `docs/images/`. Foi confirmado o arquivo `data/classifiers.csv` com 16 classificadores. Os demais artefatos citados no planejamento (README.md, CSVs de relacionamentos, atributos, métodos e chamadas, scripts Cypher e placeholder de imagens) não foram encontrados no disco no momento da escrita e devem ser criados ou revisados. Nenhum artefato foi validado em uma instância real do Neo4j e não existem prints.

Restrições gerais: Neo4j 5.x sem o plugin APOC; documentação em português; nenhum arquivo do projeto menciona a DIO.

## Glossary

- **Repositorio**: o conjunto de arquivos versionados do projeto de portfólio na pasta `c:\Develompment\WS-Personal\Neo4j_UML`.
- **README**: o arquivo `README.md` na raiz do Repositorio, documento principal de apresentação.
- **Dataset**: o conjunto de arquivos CSV na pasta `data/` que descrevem o diagrama de classes UML do domínio de e-commerce.
- **Classificador**: elemento UML do tipo classe, classe abstrata, interface ou enumeração, representado por uma linha em `data/classifiers.csv`.
- **Membro**: atributo ou método pertencente a um Classificador.
- **Relacionamento_UML**: ligação entre dois Classificadores dos tipos herança, realização (implementação de interface), associação, agregação, composição ou dependência.
- **Chamada**: invocação de um método por outro método, registrada no Dataset.
- **Pacote**: agrupamento lógico de Classificadores (por exemplo `domain`, `service`, `repository`, `infra`).
- **Script_Constraints**: o arquivo `cypher/01_constraints.cypher`, que cria constraints e índices.
- **Script_Carga**: o arquivo `cypher/02_load.cypher`, que importa o Dataset com `LOAD CSV`.
- **Script_Queries**: o arquivo `cypher/03_queries.cypher`, que contém as consultas de negócio.
- **Script_Reset**: o arquivo Cypher que remove todos os nós e relacionamentos criados pelo projeto.
- **Script_Validacao**: o conjunto de consultas Cypher que conferem as contagens esperadas após a carga.
- **Modelo_Grafo**: a documentação do esquema do grafo (labels, tipos de relacionamento e propriedades).
- **Imagem_Esquema**: imagem do Modelo_Grafo gerada pelo Arrows.app ou por `CALL db.schema.visualization()`.
- **Pergunta_Negocio**: pergunta sobre a arquitetura do sistema modelado que uma consulta do Script_Queries responde.
- **Evidencia_Visual**: captura de tela do resultado de uma consulta no Neo4j Browser, Bloom ou Explore, salva em `docs/images/`.
- **Instancia_Neo4j**: uma instalação local do Neo4j 5.x (Neo4j Desktop ou contêiner Docker) sem APOC.
- **Autor**: o mantenedor do Repositorio, responsável por executar a validação e publicar o projeto.
- **Avaliador**: pessoa que lê o Repositorio e reproduz a execução, por exemplo um recrutador técnico.

## Requirements

### Requirement 1: Estrutura do Repositório

**User Story:** Como Avaliador, quero uma estrutura de pastas previsível, para que eu encontre dados, scripts e documentação sem procurar.

#### Acceptance Criteria

1. THE Repositorio SHALL conter o arquivo `README.md` na raiz, os arquivos do Dataset em `data/`, os scripts Cypher em `cypher/` e as imagens em `docs/images/`.
2. THE Repositorio SHALL nomear cada script Cypher em `cypher/` com o padrão `NN_descricao.cypher`, onde `NN` é um número de dois dígitos (`01` a `99`) único dentro da pasta e indica a ordem de execução em ordem crescente (por exemplo `01_`, `02_`, `03_`).
3. THE Repositorio SHALL conter um arquivo `.gitignore` na raiz que exclui arquivos de sistema operacional (`.DS_Store`, `Thumbs.db`), arquivos de IDE (`.idea/`, `.vscode/`, `.vs/`) e diretórios de dados locais do Neo4j (`neo4j/data/`, `neo4j/logs/`, `neo4j/import/`).
4. THE Repositorio SHALL conter na raiz um arquivo de licença chamado `LICENSE`, com texto de licença de código aberto não vazio que identifica o ano e o titular dos direitos autorais.
5. THE README SHALL conter uma seção que lista as pastas `data/`, `cypher/` e `docs/images/`, com descrição de uma a duas frases do conteúdo de cada uma.
6. IF um arquivo exigido nos critérios 1, 3 ou 4 estiver ausente do Repositorio ou uma pasta exigida estiver vazia, THEN THE Repositorio SHALL ser considerado não conforme com este requisito, e o Avaliador SHALL identificar o item ausente pelo caminho esperado.

### Requirement 2: Contexto do Problema e Justificativa do Uso de Grafos

**User Story:** Como Avaliador, quero entender o problema e por que um grafo é adequado, para que eu avalie a decisão técnica do autor.

#### Acceptance Criteria

1. THE README SHALL conter uma seção de contexto, com 100 a 300 palavras, que descreve o problema de analisar a estrutura de um sistema orientado a objetos a partir do seu diagrama de classes UML e cita ao menos três perguntas de análise que o projeto responde (herança transitiva, análise de impacto e detecção de ciclos).
2. THE README SHALL conter uma seção de justificativa que compara o modelo em grafo com o modelo relacional, em formato de tabela ou lista, cobrindo cada uma das três consultas (herança transitiva, análise de impacto e detecção de ciclos) com ao menos um critério de comparação por consulta (por exemplo, número de junções necessárias ou forma de expressar profundidade variável).
3. THE README SHALL apresentar, na seção de justificativa, ao menos um exemplo de consulta Cypher de caminho de profundidade variável, em bloco de código, seguido de um bloco de código com a consulta SQL equivalente que usa junções recursivas, ambos referentes à mesma pergunta de análise.
4. THE README SHALL descrever o domínio de exemplo de e-commerce, listando todos os Pacotes presentes em `classifiers.csv` e, para cada Pacote, uma descrição do seu papel com 1 a 2 frases.
5. IF uma ou mais das seções exigidas (seção de contexto, seção de justificativa e descrição do domínio) estiverem ausentes do README, inclusive simultaneamente, THEN THE README SHALL ser reportado pelo Avaliador como uma única não conformidade agregada a este requisito, e SHALL NOT ser reportado como uma violação separada por seção ausente.

### Requirement 3: Instruções de Execução

**User Story:** Como Avaliador, quero instruções passo a passo, para que eu reproduza o grafo em uma Instancia_Neo4j local sem ajuda do autor.

#### Acceptance Criteria

1. THE README SHALL listar os pré-requisitos de execução, incluindo a versão mínima do Neo4j (5.0 ou superior na série 5.x), a declaração de que o APOC não é necessário e a lista dos arquivos do Dataset que devem estar disponíveis.
2. THE README SHALL descrever a execução em Neo4j Desktop como uma lista numerada de passos, incluindo como copiar os arquivos do Dataset para a pasta `import` da Instancia_Neo4j e como abrir o Neo4j Browser para executar os scripts.
3. THE README SHALL descrever a execução em Docker com um único comando completo que publica as portas HTTP e Bolt, define as credenciais de acesso e monta a pasta `data/` como pasta `import` da Instancia_Neo4j.
4. THE README SHALL listar a ordem de execução dos scripts como uma lista numerada: 1) Script_Constraints, 2) Script_Carga, 3) Script_Validacao e 4) Script_Queries, indicando o nome do arquivo de cada script.
5. THE README SHALL informar, em uma tabela, as contagens esperadas de nós por label e de relacionamentos por tipo após a carga, iguais às contagens retornadas pelo Script_Validacao sobre o Dataset.
6. THE README SHALL descrever como executar o Script_Reset para recomeçar a carga do zero, informando que o script remove todos os nós, relacionamentos e constraints criados pelos scripts e que, após a execução, a ordem do critério 4 pode ser repetida desde o início.
7. IF as contagens retornadas pelo Script_Validacao forem diferentes das contagens esperadas do critério 5, THEN THE README SHALL instruir o Avaliador a executar o Script_Reset e repetir a ordem de execução do critério 4.
8. IF o Script_Carga não encontrar os arquivos do Dataset na pasta `import`, THEN THE README SHALL orientar o Avaliador a conferir a cópia ou a montagem dos arquivos conforme os critérios 2 e 3 e a executar novamente o Script_Carga.

### Requirement 4: Troubleshooting

**User Story:** Como Avaliador, quero conhecer as dificuldades encontradas e as soluções aplicadas, para que eu resolva problemas sozinho e avalie a maturidade do autor.

#### Acceptance Criteria

1. THE README SHALL conter uma seção de troubleshooting com no mínimo cinco problemas e no máximo quinze problemas, cada um apresentado com os três campos rotulados "Sintoma", "Causa" e "Solução", sendo que o campo "Solução" contém ao menos um comando, uma configuração ou um passo executável.
2. THE README SHALL incluir, na seção de troubleshooting, o problema de arquivo CSV não encontrado pelo `LOAD CSV` por estar fora da pasta `import` da Instancia_Neo4j, com a solução indicando onde copiar os arquivos CSV e como referenciá-los no `LOAD CSV`.
3. THE README SHALL incluir, na seção de troubleshooting, o problema de valores booleanos e numéricos importados como texto pelo `LOAD CSV`, com a solução indicando a conversão explícita de tipo aplicada no Script_Carga.
4. THE README SHALL incluir, na seção de troubleshooting, o problema de tipos de relacionamento dinâmicos sem APOC, com a solução adotada no Script_Carga para criar cada tipo de relacionamento sem uso do APOC.
5. THE README SHALL incluir, na seção de troubleshooting, o problema de nós duplicados causados por reexecução da carga com `CREATE`, com a solução indicando como limpar os dados existentes ou como tornar a carga repetível, e uma consulta que permita verificar a contagem de nós após a correção.
6. THE README SHALL registrar, na seção de troubleshooting, ao menos um problema real observado durante a validação na Instancia_Neo4j descrita no Requirement 10, usando o mesmo formato de Sintoma, Causa e Solução.
7. IF um problema registrado na seção de troubleshooting não tiver sido observado durante a validação descrita no Requirement 10, THEN THE README SHALL identificá-lo como "problema potencial" e identificar como "observado" cada problema efetivamente ocorrido na validação.

### Requirement 5: Dataset de Amostra

**User Story:** Como Avaliador, quero um Dataset pequeno e consistente, para que a carga seja rápida e os resultados sejam fáceis de conferir.

#### Acceptance Criteria

1. THE Dataset SHALL conter os arquivos `classifiers.csv`, `relationships.csv`, `attributes.csv`, `methods.csv` e `calls.csv`, todos codificados em UTF-8 com linha de cabeçalho e com ao menos 1 linha de dados cada.
2. THE Dataset SHALL manter em `classifiers.csv` as colunas `id`, `name`, `kind`, `isAbstract` e `package` e exatamente 16 Classificadores, cada um com `id` não vazio e único no arquivo.
3. THE Dataset SHALL referenciar em `relationships.csv`, `attributes.csv` e `methods.csv` apenas identificadores de Classificador presentes em `classifiers.csv`, de modo que 100% das referências de origem e destino possam ser resolvidas.
4. THE Dataset SHALL referenciar em `calls.csv` apenas identificadores de método presentes em `methods.csv`, de modo que 100% das referências de método chamador e chamado possam ser resolvidas.
5. THE Dataset SHALL conter ao menos 1 Relacionamento_UML de cada tipo: herança, realização, associação, agregação, composição e dependência.
6. THE Dataset SHALL conter ao menos 1 ciclo de dependência formado por 2 a 5 Classificadores distintos, de modo que a Pergunta_Negocio de ciclos retorne ao menos 1 resultado.
7. THE Dataset SHALL conter ao menos 1 Relacionamento_UML de dependência de um Classificador do Pacote `domain` para um Classificador do Pacote `infra`, de modo que a Pergunta_Negocio de violação de camadas retorne ao menos 1 resultado.
8. THE Dataset SHALL registrar em `relationships.csv`, nas colunas `role` e `multiplicity`, o papel e a multiplicidade em notação UML (por exemplo `1`, `0..1`, `0..*`, `1..*`), não vazios, para 100% dos Relacionamentos_UML de associação, agregação e composição.
9. THE Dataset SHALL conter no máximo 200 linhas de dados em cada arquivo CSV.
10. WHEN o Avaliador carrega os cinco arquivos em um banco Neo4j vazio, THE Dataset SHALL ser carregado em até 30 segundos e sem nenhum erro de carga.

### Requirement 6: Constraints e Índices

**User Story:** Como desenvolvedor, quero constraints de unicidade antes da carga, para que a importação seja consistente e performática.

#### Acceptance Criteria

1. THE Script_Constraints SHALL criar exatamente uma constraint de unicidade sobre a propriedade identificadora de cada label de nó do Modelo_Grafo que recebe dados do Dataset, de modo que o número de constraints criadas seja igual ao número de labels listadas no Modelo_Grafo.
2. THE Script_Constraints SHALL usar a sintaxe `CREATE CONSTRAINT ... IF NOT EXISTS` do Neo4j 5.x em todos os comandos de criação de constraint ou índice.
3. WHEN o Script_Constraints é executado duas vezes seguidas na mesma Instancia_Neo4j, THE Instancia_Neo4j SHALL concluir a segunda execução com 0 erros e com a mesma contagem de constraints e índices existente após a primeira execução.
4. THE Script_Constraints SHALL conter, imediatamente antes de cada comando de criação de constraint ou índice, um comentário de linha que descreve o propósito desse comando.
5. WHEN o Script_Constraints é executado, THE Script_Constraints SHALL ser executado antes de qualquer comando de carga de dados do Dataset.
6. IF o Dataset contém dois ou mais nós com o mesmo valor do identificador para uma mesma label após a criação da constraint, THEN THE Instancia_Neo4j SHALL rejeitar a gravação do nó duplicado com erro de violação de unicidade e SHALL preservar o nó já existente sem alteração.

### Requirement 7: Script de Carga com LOAD CSV

**User Story:** Como desenvolvedor, quero um script de carga comentado e idempotente, para que eu entenda cada etapa e possa reexecutá-lo com segurança.

#### Acceptance Criteria

1. WHEN o Script_Carga é executado, THE Script_Carga SHALL importar cada um dos arquivos do Dataset (`classifiers.csv`, `relationships.csv`, `attributes.csv`, `methods.csv` e `calls.csv`) usando `LOAD CSV WITH HEADERS FROM 'file:///<arquivo>.csv'`, de modo que 100% das linhas de dados de cada arquivo sejam processadas.
2. THE Script_Carga SHALL usar `MERGE` em todos os nós e em todos os relacionamentos, e SHALL NOT usar `CREATE` para nós ou relacionamentos do Dataset.
3. WHEN o Script_Carga lê uma linha do Dataset, THE Script_Carga SHALL converter as colunas booleanas para o tipo booleano e as colunas numéricas para o tipo inteiro antes de gravar as propriedades.
4. IF uma coluna booleana ou numérica contém valor vazio ou não conversível, THEN THE Script_Carga SHALL gravar a propriedade como nula (ausente) sem interromper a importação das demais linhas, e SHALL NOT gravar o texto original como string.
5. THE Script_Carga SHALL criar cada tipo de Relacionamento_UML como um tipo de relacionamento Neo4j distinto, usando apenas Cypher nativo e SHALL NOT invocar nenhum procedimento APOC.
6. THE Script_Carga SHALL conter, imediatamente antes de cada bloco de importação, um comentário que descreve o arquivo lido, os nós ou relacionamentos criados e as conversões aplicadas.
7. WHEN o Script_Carga é executado duas vezes seguidas sobre a mesma Instancia_Neo4j sem alteração do Dataset, THE Instancia_Neo4j SHALL apresentar contagens de nós (total e por label) e de relacionamentos (total e por tipo) idênticas após a primeira e após a segunda execução.
8. IF o Script_Carga falha durante a execução (por exemplo, arquivo do Dataset não encontrado), THEN THE Script_Carga SHALL encerrar com mensagem de erro do Neo4j indicando a causa, THE Instancia_Neo4j SHALL manter no grafo, sem rollback, os nós e relacionamentos já gravados antes da falha, e a nova execução do Script_Carga SHALL completar o estado do grafo por meio de `MERGE`, sem duplicar nós ou relacionamentos e sem exigir execução prévia do Script_Reset.
9. WHEN o Script_Reset é executado, THE Script_Reset SHALL remover todos os nós e relacionamentos do grafo do projeto, de modo que a contagem total de nós e a de relacionamentos sejam iguais a 0 ao final.
10. WHEN o Script_Validacao é executado após o Script_Carga, THE Script_Validacao SHALL retornar uma linha por label com a contagem de nós e uma linha por tipo de relacionamento com a contagem de relacionamentos, e THE README SHALL apresentar os valores esperados dessas contagens, que SHALL ser iguais aos retornados pelo Script_Validacao.

### Requirement 8: Modelo do Grafo

**User Story:** Como Avaliador, quero ver o esquema do grafo, para que eu entenda labels, relacionamentos e propriedades antes de ler as consultas.

#### Acceptance Criteria

1. THE Modelo_Grafo SHALL documentar, para 100% dos labels de nó existentes na Instancia_Neo4j após a carga, o nome do label, a lista de propriedades, o tipo de dado de cada propriedade e a propriedade que atua como identificador único.
2. THE Modelo_Grafo SHALL documentar, para 100% dos tipos de relacionamento existentes na Instancia_Neo4j após a carga, o nome do tipo, o label de origem, o label de destino, a direção e a lista de propriedades (ou a indicação explícita "sem propriedades").
3. THE Modelo_Grafo SHALL documentar o mapeamento de cada um dos cinco conceitos UML (Classificador, Membro, Relacionamento_UML, Chamada, Pacote) para exatamente um ou mais labels ou tipos de relacionamento do grafo, indicando para cada conceito o elemento correspondente.
4. THE Repositorio SHALL conter em `docs/images/` ao menos uma Imagem_Esquema, em formato PNG, gerada por `CALL db.schema.visualization()` na Instancia_Neo4j após a carga, mostrando todos os labels e tipos de relacionamento documentados no Modelo_Grafo.
5. THE Repositorio SHALL conter em `docs/images/` uma Imagem_Esquema do Arrows.app, em formato PNG, que mostra as propriedades de cada label e de cada tipo de relacionamento, e o arquivo de exportação do Arrows.app correspondente, em formato JSON.
6. THE README SHALL exibir cada Imagem_Esquema por meio de link relativo para `docs/images/` que resolve para um arquivo existente no Repositorio.
7. THE Modelo_Grafo SHALL usar labels em PascalCase, tipos de relacionamento em UPPER_SNAKE_CASE e propriedades em camelCase, sem exceções em nenhum elemento documentado.
8. IF um label, tipo de relacionamento ou propriedade existente na Instancia_Neo4j após a carga não constar na documentação do Modelo_Grafo, THEN THE Modelo_Grafo SHALL ser considerado incompleto e o Avaliador SHALL poder identificar a divergência comparando a documentação com o resultado de `CALL db.schema.visualization()`.

### Requirement 9: Perguntas de Negócio e Consultas

**User Story:** Como Avaliador, quero perguntas de negócio respondidas pelo grafo, para que eu veja o valor prático da modelagem.

#### Acceptance Criteria

1. THE Script_Queries SHALL conter ao menos oito Perguntas_Negocio, cada uma com um comentário que enuncia a pergunta em português, com no máximo 200 caracteres, seguido da consulta Cypher que a responde.
2. THE Script_Queries SHALL incluir uma Pergunta_Negocio de hierarquia de herança transitiva que retorna todos os Classificadores ancestrais de um Classificador informado, percorrendo uma ou mais relações de herança (profundidade mínima 1, sem limite superior fixo), sem repetir Classificadores no resultado.
3. THE Script_Queries SHALL incluir uma Pergunta_Negocio que retorna os Classificadores concretos (não interface e não abstratos) que implementam uma interface informada, direta ou indiretamente, incluindo implementação por meio de herança de um ancestral que implementa a interface, sem repetir Classificadores no resultado.
4. THE Script_Queries SHALL incluir uma Pergunta_Negocio de análise de impacto que lista, sem repetição, os Classificadores que dependem, de forma transitiva, de um Classificador informado, e que exclui o próprio Classificador informado do resultado.
5. THE Script_Queries SHALL incluir uma Pergunta_Negocio de detecção de ciclos de dependência que retorna, para cada ciclo encontrado, a lista ordenada dos Classificadores participantes, e que retorna zero linhas quando não existe ciclo.
6. THE Script_Queries SHALL incluir uma Pergunta_Negocio de violação de camadas que lista cada dependência cujo Classificador de origem pertence ao Pacote `domain` e cujo Classificador de destino pertence a um dos Pacotes `service`, `repository` ou `infra`, retornando o Classificador de origem, o Classificador de destino e o Pacote de destino.
7. THE Script_Queries SHALL incluir uma Pergunta_Negocio de acoplamento que retorna, para cada Classificador, o número de relacionamentos de entrada, o número de relacionamentos de saída e o total, ordenados de forma decrescente pelo total e, em caso de empate, de forma crescente pelo nome do Classificador.
8. THE Script_Queries SHALL incluir uma Pergunta_Negocio de cadeia de Chamadas que retorna os métodos alcançáveis por Chamadas, de forma transitiva, a partir de um método informado, com profundidade máxima de 10 níveis, sem repetir métodos no resultado.
9. THE Script_Queries SHALL definir, com `:param`, os valores de entrada de cada consulta parametrizada e referenciá-los nas consultas com a sintaxe `$parametro`, sem valores literais fixos para essas entradas.
10. THE README SHALL conter uma tabela com uma linha para cada Pergunta_Negocio do Script_Queries e as colunas: Pergunta_Negocio, consulta do Script_Queries, resultado esperado (valores concretos retornados pela carga dos CSVs) e Evidencia_Visual correspondente.
11. WHEN cada consulta do Script_Queries é executada na Instancia_Neo4j após a carga, THE Instancia_Neo4j SHALL retornar, sem erro, um resultado idêntico ao resultado esperado documentado no README para essa consulta.
12. IF uma consulta parametrizada do Script_Queries é executada sem o `:param` correspondente definido, THEN THE Instancia_Neo4j SHALL rejeitar a execução com um erro indicando o parâmetro ausente e não SHALL alterar os dados do grafo.

### Requirement 10: Validação em Instância Real

**User Story:** Como Autor, quero validar todos os scripts em uma Instancia_Neo4j real, para que o Repositorio não publique código não testado.

#### Acceptance Criteria

1. WHEN o Autor prepara a publicação do Repositorio, THE Autor SHALL executar o Script_Constraints, o Script_Carga, o Script_Validacao, o Script_Queries e o Script_Reset, nesta ordem, em uma Instancia_Neo4j com banco vazio, e cada script SHALL terminar com 0 erros reportados pelo Neo4j.
2. WHEN o Script_Reset termina na validação, THE Autor SHALL executar novamente o Script_Carga e o Script_Validacao na mesma Instancia_Neo4j, e ambos SHALL terminar com 0 erros e com os mesmos resultados da primeira execução.
3. IF uma consulta do Script_Validacao ou do Script_Queries retorna resultado diferente do resultado esperado documentado (número de linhas, valores ou contagens), THEN THE Autor SHALL corrigir o Dataset, o script ou o resultado esperado documentado, reexecutar a sequência completa do critério 1 e registrar o caso na seção de troubleshooting do README com a consulta afetada, o resultado obtido, o resultado esperado e a correção aplicada.
4. THE README SHALL informar a versão exata do Neo4j usada na validação no formato MAJOR.MINOR.PATCH (por exemplo, 5.26.0), a edição (Community ou Enterprise) e a data da validação.
5. IF a sequência completa do critério 1 não termina com 0 erros, THEN THE Autor SHALL NOT publicar o Repositorio até que uma execução completa termine com 0 erros.

### Requirement 11: Evidências Visuais

**User Story:** Como Avaliador, quero prints dos resultados, para que eu confira o funcionamento sem precisar executar o projeto.

#### Acceptance Criteria

1. THE Repositorio SHALL conter em `docs/images/` exatamente uma Evidencia_Visual para cada Pergunta_Negocio do Script_Queries, e nenhuma Pergunta_Negocio SHALL ficar sem Evidencia_Visual.
2. THE Repositorio SHALL nomear cada Evidencia_Visual com o padrão `qNN-descricao-em-kebab-case.png`, em que NN é um número de 2 dígitos (01 a 99) igual ao número da Pergunta_Negocio correspondente no Script_Queries, e a descrição contém de 1 a 60 caracteres em letras minúsculas sem acentos, dígitos e hífens (por exemplo `q01-hierarquia-heranca.png`).
3. THE Repositorio SHALL conter ao menos 1 Evidencia_Visual em modo grafo (nós e relacionamentos desenhados) e ao menos 1 Evidencia_Visual em modo tabela (linhas e colunas).
4. THE README SHALL exibir cada Evidencia_Visual imediatamente abaixo do título e do texto da Pergunta_Negocio correspondente, com texto alternativo de 10 a 150 caracteres que descreva a Pergunta_Negocio e o tipo de resultado (grafo ou tabela).
5. THE Repositorio SHALL conter cada Evidencia_Visual em formato PNG com largura mínima de 1200 pixels, tamanho máximo de 5 MB por arquivo, exibindo simultaneamente o texto completo da consulta Cypher e o resultado, com texto legível sem ampliação acima de 100% em tela de 1920 x 1080 pixels.
6. THE Repositorio SHALL conter Evidencias_Visuais sem dados pessoais, credenciais ou URLs de instâncias privadas, de modo que nenhuma imagem exiba nome de pessoa, e-mail, senha, token, endereço IP ou nome de host de instância privada.
7. IF uma Pergunta_Negocio do Script_Queries não possuir arquivo de Evidencia_Visual em `docs/images/` ou o README referenciar um arquivo inexistente, THEN THE Repositorio SHALL ser considerado não conforme com este requisito, e o Avaliador SHALL poder identificar a Pergunta_Negocio afetada pelo prefixo numérico `qNN`.

### Requirement 12: Restrições de Conteúdo

**User Story:** Como Autor, quero um conteúdo autoral e consistente, para que o Repositorio represente meu trabalho de forma profissional.

#### Acceptance Criteria

1. THE Repositorio SHALL conter zero ocorrências, sem distinção entre maiúsculas e minúsculas, do termo "DIO" como palavra isolada ou do termo "Digital Innovation One", em documentos, comentários de código, nomes de arquivo e metadados de imagem (EXIF, XMP e campos de texto PNG).
2. THE Repositorio SHALL conter README, Modelo_Grafo e comentários dos scripts Cypher escritos em português do Brasil, com exceção de identificadores técnicos, palavras-chave Cypher, nomes de comandos e nomes de produtos.
3. THE Repositorio SHALL conter scripts Cypher que executam do início ao fim em Neo4j 5.x sem erro e sem chamadas a procedimentos ou funções com prefixo `apoc.`.
4. IF um script Cypher contiver chamada a procedimento ou função com prefixo `apoc.`, THEN THE Repositorio SHALL ser considerado não conforme com este requisito.
5. THE Repositorio SHALL conter zero arquivos com senhas, tokens ou chaves reais, incluindo arquivos de configuração, scripts, README e histórico de commits da branch entregue.
6. WHEN o README apresentar um comando que exige credenciais, THE README SHALL usar valores de exemplo em formato de marcador explícito (por exemplo, `<sua-senha>`) acompanhados de texto indicando que o valor é um exemplo a ser substituído pelo usuário.
