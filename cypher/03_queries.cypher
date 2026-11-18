// 03_queries.cypher
// Oito perguntas de negócio (Q01-Q08) sobre o grafo UML de e-commerce.
// Somente leitura. Cypher nativo, sem uso de procedimentos APOC
// Execute no Neo4j Browser ou no cypher-shell: ":param" é comando do cliente, não Cypher.
// Execute depois de 01_constraints e 02_load. Sem o :param correspondente, a consulta
// falha com erro de parâmetro ausente e nada é alterado.

// ---------------------------------------------------------------------------
// Parâmetros de entrada (altere aqui, nunca dentro das consultas)
// ---------------------------------------------------------------------------
:param nome => 'CreditCardPayment'
:param interface => 'PaymentGateway'
:param metodo => 'OrderService.placeOrder'
:param pacote => 'domain'

// Q01 - Quais são todos os ancestrais (diretos e indiretos) de um classificador, sem repetição?
MATCH (:Classifier {name: $nome})-[:EXTENDS*1..]->(a:Classifier)
RETURN DISTINCT a.name AS ancestral
ORDER BY ancestral;

// Q02 - Quais classes concretas implementam uma interface, direta ou por herança de um ancestral que a implementa?
MATCH (:Interface {name: $interface})<-[:IMPLEMENTS]-(:Classifier)<-[:EXTENDS*0..]-(c:Classifier)
WHERE NOT c:Interface
  AND coalesce(c.isAbstract, false) = false
RETURN DISTINCT c.name AS implementacaoConcreta
ORDER BY implementacaoConcreta;

// Q03 - Quem é impactado, de forma transitiva, se um classificador mudar (quem depende dele)?
MATCH (d:Classifier)-[:DEPENDS_ON*1..]->(:Classifier {name: $nome})
WHERE d.name <> $nome
RETURN DISTINCT d.name AS impactado
ORDER BY impactado;

// Q04 - Existem ciclos de dependência entre classificadores? Quais participantes formam cada ciclo?
// Nós distintos no ciclo; cada ciclo sai uma vez, iniciando pelo menor id (sem rotações repetidas).
MATCH p = (a:Classifier)-[:DEPENDS_ON*2..5]->(a)
WITH [n IN nodes(p)[0..-1] | n.id] AS ids,
     [n IN nodes(p)[0..-1] | n.name] AS nomes
WHERE size(ids) = size(reduce(vistos = [], x IN ids | CASE WHEN x IN vistos THEN vistos ELSE vistos + x END))
  AND all(x IN ids WHERE ids[0] <= x)
RETURN nomes AS ciclo;

// Q05 - Quais dependências violam as camadas (pacote domain dependendo de service, repository ou infra)?
MATCH (po:Package {name: 'domain'})-[:CONTAINS]->(origem:Classifier)-[:DEPENDS_ON]->(destino:Classifier)<-[:CONTAINS]-(pd:Package)
WHERE pd.name IN ['service', 'repository', 'infra']
RETURN origem.name AS origem, destino.name AS destino, pd.name AS pacoteDestino
ORDER BY origem, destino;

// Q06 - Quais classificadores são mais acoplados (relacionamentos de entrada, saída e total)?
// Contam para o acoplamento apenas relacionamentos entre classificadores dos tipos
// EXTENDS, IMPLEMENTS, DEPENDS_ON, ASSOCIATES, COMPOSED_OF e AGGREGATES.
// CONTAINS, HAS_ATTRIBUTE, HAS_METHOD e CALLS ficam de fora (não ligam classificadores entre si).
// Ordenação: total decrescente e, em empate, nome crescente.
MATCH (c:Classifier)
WITH c,
     COUNT { (c)<-[:EXTENDS|IMPLEMENTS|DEPENDS_ON|ASSOCIATES|COMPOSED_OF|AGGREGATES]-(:Classifier) } AS entrada,
     COUNT { (c)-[:EXTENDS|IMPLEMENTS|DEPENDS_ON|ASSOCIATES|COMPOSED_OF|AGGREGATES]->(:Classifier) } AS saida
RETURN c.name AS classificador, entrada, saida, entrada + saida AS total
ORDER BY total DESC, classificador ASC;

// Q07 - Quais métodos são disparados, de forma transitiva (até 10 níveis), a partir de um método?
MATCH (:Method {id: $metodo})-[:CALLS*1..10]->(m:Method)
RETURN DISTINCT m.id AS metodoAlcancado
ORDER BY metodoAlcancado;

// Q08 - Qual é a estrutura de um pacote: seus classificadores, atributos e métodos?
MATCH (:Package {name: $pacote})-[:CONTAINS]->(c:Classifier)
OPTIONAL MATCH (c)-[:HAS_ATTRIBUTE]->(at:Attribute)
OPTIONAL MATCH (c)-[:HAS_METHOD]->(me:Method)
RETURN c, at, me;
