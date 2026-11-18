# Diagrama de Classes UML em Grafo com Neo4j

Portfólio que modela um diagrama de classes UML de um sistema de e-commerce como um banco de dados em grafo no Neo4j 5.x, sem o plugin APOC. O repositório traz o dataset em CSV, os scripts Cypher de carga e consulta e as evidências visuais dos resultados.

## Estrutura de pastas

- `data/`: arquivos CSV do dataset que descrevem o diagrama de classes (classificadores, relacionamentos, atributos, métodos e chamadas). É a fonte lida pelo `LOAD CSV`.
- `cypher/`: scripts Cypher numerados na ordem de execução (`NN_descricao.cypher`), cobrindo constraints, carga, validação, consultas de negócio e reset.
- `docs/images/`: imagens do esquema do grafo e capturas de tela dos resultados das consultas.

## Contexto

Em um sistema orientado a objetos, a estrutura do código cresce a ponto de ficar difícil responder, só lendo o diagrama de classes UML, como as peças se relacionam. Classes herdam de outras, interfaces são implementadas por vários tipos e dependências se acumulam entre camadas. Este projeto trata o diagrama como um grafo, em que classificadores são nós e relacionamentos UML são arestas, e responde três perguntas de análise.

A primeira é a herança transitiva: quais são todos os ancestrais de uma classe, seguindo a cadeia de herança por quantos níveis existirem. A segunda é a análise de impacto: quais classificadores são afetados, direta ou indiretamente, se um determinado classificador mudar. A terceira é a detecção de ciclos: quais grupos de classificadores dependem uns dos outros em círculo, um sinal de acoplamento indesejado. As três exigem percorrer caminhos de profundidade desconhecida, que é o ponto forte de um banco em grafo.

## Justificativa: grafo versus relacional

Em um modelo relacional, cada salto na hierarquia exige uma nova junção da tabela de relacionamentos com ela mesma, ou uma consulta recursiva. No grafo, o caminho é expresso diretamente no padrão da consulta.

| Consulta | Grafo (Cypher) | Relacional (SQL) |
|---|---|---|
| Herança transitiva | Um padrão `-[:EXTENDS*1..]->` cobre qualquer profundidade. | Uma junção por nível, ou CTE recursiva com `UNION ALL` e controle de repetição. |
| Análise de impacto | Um padrão `<-[:DEPENDS_ON*1..]-` percorre as dependências no sentido inverso, sem junções extras. | CTE recursiva sobre a tabela de relacionamentos, com `DISTINCT` para remover duplicatas e filtro para excluir o nó de origem. |
| Detecção de ciclos | O padrão de caminho que retorna ao nó inicial expressa o ciclo em uma única cláusula `MATCH`. | CTE recursiva que acumula o caminho percorrido (por exemplo, um array) e testa se o destino já foi visitado, com sintaxe que varia entre bancos. |

Exemplo em Cypher, para a herança transitiva de um classificador (profundidade variável, sem limite superior fixo):

```cypher
MATCH (c:Classifier {id: $classificadorId})-[:EXTENDS*1..]->(ancestral:Classifier)
RETURN DISTINCT ancestral.name AS ancestral
ORDER BY ancestral;
```

A mesma pergunta em SQL, com junção recursiva sobre uma tabela `relationships(source_id, target_id, type)`:

```sql
WITH RECURSIVE ancestrais AS (
    SELECT r.target_id AS id
    FROM relationships r
    WHERE r.source_id = :classificador_id
      AND r.type = 'EXTENDS'
  UNION
    SELECT r.target_id
    FROM relationships r
    JOIN ancestrais a ON r.source_id = a.id
    WHERE r.type = 'EXTENDS'
)
SELECT c.name AS ancestral
FROM ancestrais a
JOIN classifiers c ON c.id = a.id
ORDER BY c.name;
```

## Domínio de exemplo

O domínio é um sistema de e-commerce com 16 classificadores, organizados em quatro pacotes:

- `domain`: entidades e tipos do negócio, como clientes, pedidos, itens, produtos e pagamentos. Concentra as regras centrais e deveria ser o pacote mais independente.
- `service`: serviços de aplicação que orquestram os casos de uso, como pedidos, pagamentos e notificações, e a interface do gateway de pagamento.
- `repository`: interfaces de acesso a dados que abstraem a persistência de pedidos e clientes.
- `infra`: implementações concretas de infraestrutura, como o gateway de pagamento, o repositório de pedidos e o envio de e-mail.

## Como executar

### Pré-requisitos

- Neo4j 5.0 ou superior, dentro da série 5.x (Neo4j Desktop ou contêiner Docker).
- O plugin APOC não é necessário. Os scripts usam apenas Cypher nativo.
- Os cinco arquivos do dataset, que devem estar disponíveis na pasta `import` da instância: `classifiers.csv`, `relationships.csv`, `attributes.csv`, `methods.csv` e `calls.csv` (todos em `data/`).

### Execução no Neo4j Desktop

1. Crie uma instância local do Neo4j 5.x (sem instalar plugins) e inicie-a.
2. No Neo4j Desktop, abra o menu da instância e escolha a opção para abrir a pasta `import` (Open folder, Import).
3. Copie os cinco arquivos de `data/` para essa pasta `import`.
4. Abra o Neo4j Browser a partir da instância (botão Open).
5. Execute os scripts de `cypher/` na ordem descrita em [Ordem de execução dos scripts](#ordem-de-execução-dos-scripts). No Neo4j Browser, cole o conteúdo de cada arquivo e execute os comandos um a um.

### Execução com Docker

Execute o comando abaixo na raiz do repositório (funciona em bash e em PowerShell). Ele publica a interface HTTP (7474) e o Bolt (7687), define as credenciais e monta `data/` como pasta `import` da instância.

```bash
docker run --name neo4j-uml -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/<sua-senha> -v "${PWD}/data:/var/lib/neo4j/import" neo4j:5
```

> **Atenção:** `<sua-senha>` é apenas um marcador de exemplo. Substitua pelo valor de uma senha sua (o Neo4j exige ao menos 8 caracteres) e não registre a senha real em arquivos do repositório.

Depois, abra `http://localhost:7474` no navegador e entre com o usuário `neo4j` e a senha escolhida.

### Ordem de execução dos scripts

Na primeira vez, execute os scripts nesta ordem. O `04_validate` é somente leitura e deve rodar logo após a carga, antes das consultas.

1. `cypher/01_constraints.cypher`: cria as constraints de unicidade.
2. `cypher/02_load.cypher`: importa os CSVs com `LOAD CSV`.
3. `cypher/04_validate.cypher`: confere as contagens de nós e relacionamentos (somente leitura).
4. `cypher/03_queries.cypher`: executa as oito perguntas de negócio (Q01 a Q08).

### Contagens esperadas após a carga

Valores calculados sobre os CSVs reais de `data/` com o oráculo `tests/helpers/oracles.py`. O `04_validate.cypher` deve retornar os mesmos números. Um nó de classificador aparece em `Classifier` e também no label do seu tipo, por isso `Classifier` (16) é igual a `Class` + `Interface` + `Enum` (12 + 3 + 1).

| Label | Nós esperados |
|---|---|
| `Package` | 4 |
| `Classifier` | 16 |
| `Class` | 12 |
| `Interface` | 3 |
| `Enum` | 1 |
| `Attribute` | 18 |
| `Method` | 17 |

| Tipo de relacionamento | Relacionamentos esperados |
|---|---|
| `CONTAINS` | 16 |
| `HAS_ATTRIBUTE` | 18 |
| `HAS_METHOD` | 17 |
| `EXTENDS` | 1 |
| `IMPLEMENTS` | 2 |
| `DEPENDS_ON` | 9 |
| `ASSOCIATES` | 3 |
| `COMPOSED_OF` | 1 |
| `AGGREGATES` | 1 |
| `CALLS` | 8 |

### Recomeçar do zero (reset)

O `cypher/99_reset.cypher` remove os nós do projeto (`Package`, `Classifier`, `Attribute` e `Method`) com todos os seus relacionamentos e também as constraints criadas pelo `01_constraints`. Depois de executá-lo, repita a [ordem de execução](#ordem-de-execução-dos-scripts) desde o início (`01_constraints`, `02_load`, `04_validate`, `03_queries`).

Se as contagens do `04_validate` forem diferentes das tabelas acima, execute o `99_reset.cypher` e repita a ordem de execução.

Se o `02_load` falhar por não encontrar os arquivos CSV, confira se os cinco arquivos estão na pasta `import` (cópia no Neo4j Desktop ou montagem `-v` no Docker, conforme as seções acima) e execute o `02_load` novamente. A carga usa `MERGE`, então a nova execução completa o que faltou sem duplicar dados.

## Perguntas de negócio e resultados esperados

As consultas ficam em `cypher/03_queries.cypher` e usam estes parâmetros padrão: `nome = CreditCardPayment`, `interface = PaymentGateway`, `metodo = OrderService.placeOrder` e `pacote = domain`. Os resultados esperados abaixo foram calculados com os oráculos de `tests/helpers/oracles.py` sobre os CSVs reais, com esses valores.

> **Pendente:** os resultados esperados e as evidências visuais aguardam a confirmação do Autor na validação em uma instância Neo4j real (tarefa 9.1). Os arquivos de imagem listados na última coluna são nomes planejados e ainda não existem em `docs/images/`.

| Pergunta de negócio | Consulta | Resultado esperado | Evidência visual (planejada) |
|---|---|---|---|
| Q01. Quais são todos os ancestrais de um classificador? | Q01 em `03_queries.cypher` | 1 linha: `Payment` | `q01-hierarquia-heranca.png` |
| Q02. Quais classes concretas implementam uma interface, direta ou por herança? | Q02 | 1 linha: `StripeGateway` | `q02-implementacoes-interface.png` |
| Q03. Quem é impactado, de forma transitiva, se um classificador mudar? | Q03 | 0 linhas: nenhum classificador depende de `CreditCardPayment` | `q03-analise-impacto.png` |
| Q04. Existem ciclos de dependência? | Q04 | 1 ciclo: `[NotificationService, OrderService, PaymentService]` | `q04-ciclos-dependencia.png` |
| Q05. Quais dependências violam as camadas? | Q05 | 1 linha: origem `Payment`, destino `StripeGateway`, pacote `infra` | `q05-violacao-camadas.png` |
| Q06. Quais classificadores são mais acoplados? | Q06 | 16 linhas, ordenadas por total decrescente e nome crescente. Primeiras linhas (classificador, entrada, saída, total): `Payment` 3, 2, 5; `Order` 2, 2, 4; `PaymentService` 1, 3, 4; `NotificationService` 1, 2, 3; `OrderService` 1, 2, 3. Última linha: `CustomerRepository` 0, 0, 0 | `q06-acoplamento.png` |
| Q07. Quais métodos são disparados a partir de um método? | Q07 | 8 linhas: `JpaOrderRepository.save`, `NotificationService.sendReceipt`, `Order.calculateTotal`, `OrderItem.subtotal`, `OrderRepository.save`, `PaymentService.charge`, `SmtpEmailSender.send`, `StripeGateway.authorize` | `q07-cadeia-chamadas.png` |
| Q08. Qual é a estrutura de um pacote? | Q08 | Subgrafo do pacote `domain`: 7 classificadores, 13 atributos e 7 métodos (17 linhas de resultado, pela combinação de atributos e métodos de cada classificador) | `q08-estrutura-pacote.png` |

## Troubleshooting

> **Situação atual:** todos os problemas abaixo estão identificados como **problema potencial**. Eles são riscos conhecidos desta carga, mas nenhum foi observado ainda, porque o projeto não foi validado em uma instância Neo4j real. Os problemas efetivamente ocorridos na validação serão registrados como **observado**, no mesmo formato, na tarefa 10.1.

### 1. CSV não encontrado pelo `LOAD CSV` (problema potencial)

- **Sintoma:** o `02_load.cypher` falha com um erro de arquivo não encontrado, por exemplo `Couldn't load the external resource at: file:/.../import/classifiers.csv`.
- **Causa:** o `LOAD CSV ... FROM 'file:///arquivo.csv'` só lê arquivos da pasta `import` da instância. Os CSVs que estão apenas em `data/` não são visíveis para o Neo4j.
- **Solução:** copie os cinco CSVs para a pasta `import` e mantenha a URL no formato `file:///nome.csv`, sem caminho de disco. No Docker, monte `data/` como `import` com `-v "${PWD}/data:/var/lib/neo4j/import"` (comando em [Execução com Docker](#execução-com-docker)). Em instalação local, copie os arquivos (PowerShell, na raiz do repositório):

  ```powershell
  Copy-Item data\*.csv "<pasta-import-da-instancia>"
  ```

  Depois execute o `02_load.cypher` novamente. A carga usa `MERGE`, então a nova execução completa o que faltou.

### 2. Booleanos e números importados como texto (problema potencial)

- **Sintoma:** filtros como `WHERE c.isAbstract = true` não retornam nada, ou `ORDER BY a.position` ordena `"10"` antes de `"2"`. Ao inspecionar o nó, as propriedades aparecem entre aspas.
- **Causa:** o `LOAD CSV` entrega todas as colunas como `String`. Gravar `row.isAbstract` ou `row.position` direto no nó preserva o texto.
- **Solução:** converta explicitamente, como o `02_load.cypher` já faz: `toBooleanOrNull(row.isAbstract)` para booleanos e `toIntegerOrNull(row.position)` para inteiros. Valor vazio ou inválido vira nulo, e o texto original não é gravado. Para conferir os tipos depois da carga:

  ```cypher
  MATCH (c:Classifier)
  RETURN valueType(c.isAbstract) AS tipo, count(*) AS total;
  ```

  O resultado deve conter apenas `BOOLEAN` (ou `BOOLEAN NOT NULL`) e, se houver vazios, `NULL`. Se aparecer `STRING`, rode o `99_reset.cypher` e repita a ordem de execução com o `02_load.cypher` atual.

### 3. Tipo de relacionamento dinâmico sem APOC (problema potencial)

- **Sintoma:** ao ler `relationships.csv`, onde o tipo vem na coluna `type`, a tentativa de escrever `MERGE (a)-[r:row.type]->(b)` ou `[:$tipo]` resulta em erro de sintaxe.
- **Causa:** o Cypher não aceita o tipo de relacionamento como expressão ou parâmetro. A alternativa comum é um procedimento do plugin APOC, que este projeto não usa.
- **Solução:** use um bloco `LOAD CSV` por tipo, filtrado por `row.type`, como no `02_load.cypher`:

  ```cypher
  LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
  WITH row WHERE row.type = 'EXTENDS'
  MATCH (a:Classifier {id: row.sourceId})
  MATCH (b:Classifier {id: row.targetId})
  MERGE (a)-[:EXTENDS]->(b);
  ```

  Para um tipo novo no CSV, copie o bloco e troque o valor do filtro e o tipo do relacionamento.

### 4. Nós duplicados ao reexecutar a carga com `CREATE` (problema potencial)

- **Sintoma:** depois de executar a carga mais de uma vez, as contagens ficam acima das esperadas, por exemplo mais de 16 nós `Classifier`.
- **Causa:** o `CREATE` insere um novo nó a cada execução. Sem constraint de unicidade, nada impede a duplicata.
- **Solução:** torne a carga repetível com `MERGE` (o `02_load.cypher` já usa) e crie as constraints antes, com o `01_constraints.cypher`. Para limpar duplicatas existentes, execute o `cypher/99_reset.cypher` e repita a [ordem de execução](#ordem-de-execução-dos-scripts). Para verificar a contagem, execute:

  ```cypher
  MATCH (c:Classifier)
  RETURN count(c) AS total, count(DISTINCT c.id) AS distintos;
  ```

  O esperado é `total = 16` e `distintos = 16`. Valores diferentes indicam duplicatas.

### 5. Erro de violação de unicidade na carga (problema potencial)

- **Sintoma:** o Neo4j rejeita a gravação com `already exists with label ... and property ...`.
- **Causa:** uma constraint de unicidade já existe e o dataset (ou um CSV editado) contém dois registros com o mesmo identificador para o mesmo label.
- **Solução:** localize o identificador repetido no CSV e corrija o arquivo, por exemplo (PowerShell, na raiz do repositório):

  ```powershell
  Import-Csv data\classifiers.csv | Group-Object id | Where-Object Count -gt 1
  ```

  Depois copie o CSV corrigido para a pasta `import` e execute o `02_load.cypher` novamente. O nó que já existia é preservado.

### 6. Constraint já existe ao repetir o `01_constraints` (problema potencial)

- **Sintoma:** erro informando que uma constraint equivalente já existe, ao executar uma instrução de criação isolada.
- **Causa:** a instrução foi escrita sem `IF NOT EXISTS`, ou foi executada fora do script do repositório.
- **Solução:** use a sintaxe do Neo4j 5.x com `IF NOT EXISTS`, como no `01_constraints.cypher`. Para listar o que existe:

  ```cypher
  SHOW CONSTRAINTS;
  ```

  Para recomeçar do zero, execute o `99_reset.cypher`.

## Validação

> **Pendente, a preencher pelo Autor na tarefa 10.1.** Os campos abaixo ficam em aberto até a validação dos scripts em uma instância Neo4j real. Nenhum valor foi inferido ou estimado.

| Campo | Valor |
|---|---|
| Versão do Neo4j (MAJOR.MINOR.PATCH) | _pendente: a preencher pelo Autor na tarefa 10.1_ |
| Edição (Community ou Enterprise) | _pendente: a preencher pelo Autor na tarefa 10.1_ |
| Data da validação | _pendente: a preencher pelo Autor na tarefa 10.1_ |
