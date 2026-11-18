// Lê classifiers.csv. Cria/atualiza nós Package (chave: name) a partir dos valores distintos da coluna package.
// Linhas com package vazio (nulo) são descartadas. Sem conversão de tipos.
LOAD CSV WITH HEADERS FROM 'file:///classifiers.csv' AS row
WITH DISTINCT row.package AS packageName
WHERE packageName IS NOT NULL
MERGE (p:Package {name: packageName});

// Lê classifiers.csv. Cria/atualiza nós Classifier (chave: id) e aplica o label secundário
// Class, Interface ou Enum conforme a coluna kind.
// Conversão: isAbstract (texto) -> booleano com toBooleanOrNull; valor vazio ou inválido vira nulo.
LOAD CSV WITH HEADERS FROM 'file:///classifiers.csv' AS row
WITH row WHERE row.id IS NOT NULL
MERGE (c:Classifier {id: row.id})
SET c.name = row.name,
    c.kind = row.kind,
    c.isAbstract = toBooleanOrNull(row.isAbstract)
FOREACH (_ IN CASE WHEN row.kind = 'class'     THEN [1] ELSE [] END | SET c:Class)
FOREACH (_ IN CASE WHEN row.kind = 'interface' THEN [1] ELSE [] END | SET c:Interface)
FOREACH (_ IN CASE WHEN row.kind = 'enum'      THEN [1] ELSE [] END | SET c:Enum);

// Lê attributes.csv. Cria/atualiza nós Attribute (chave: id).
// Conversões: isStatic (texto) -> booleano com toBooleanOrNull; position (texto) -> inteiro com
// toIntegerOrNull; valor vazio ou inválido vira nulo.
LOAD CSV WITH HEADERS FROM 'file:///attributes.csv' AS row
WITH row WHERE row.id IS NOT NULL
MERGE (a:Attribute {id: row.id})
SET a.name = row.name,
    a.dataType = row.dataType,
    a.visibility = row.visibility,
    a.isStatic = toBooleanOrNull(row.isStatic),
    a.position = toIntegerOrNull(row.position);

// Lê methods.csv. Cria/atualiza nós Method (chave: id).
// Conversões: isStatic e isAbstract (texto) -> booleano com toBooleanOrNull; position (texto) -> inteiro
// com toIntegerOrNull; valor vazio ou inválido vira nulo.
LOAD CSV WITH HEADERS FROM 'file:///methods.csv' AS row
WITH row WHERE row.id IS NOT NULL
MERGE (m:Method {id: row.id})
SET m.name = row.name,
    m.returnType = row.returnType,
    m.visibility = row.visibility,
    m.isStatic = toBooleanOrNull(row.isStatic),
    m.isAbstract = toBooleanOrNull(row.isAbstract),
    m.position = toIntegerOrNull(row.position);

// Lê classifiers.csv. Cria relacionamentos CONTAINS (Package -> Classifier) usando a coluna package.
// Linhas cujo pacote ou classificador não existe são descartadas pelo MATCH. Sem conversão de tipos.
LOAD CSV WITH HEADERS FROM 'file:///classifiers.csv' AS row
WITH row WHERE row.id IS NOT NULL AND row.package IS NOT NULL
MATCH (p:Package {name: row.package})
MATCH (c:Classifier {id: row.id})
MERGE (p)-[:CONTAINS]->(c);

// Lê attributes.csv. Cria relacionamentos HAS_ATTRIBUTE (Classifier -> Attribute) usando classifierId.
// Linhas cujo classificador ou atributo não existe são descartadas pelo MATCH. Sem conversão de tipos.
LOAD CSV WITH HEADERS FROM 'file:///attributes.csv' AS row
WITH row WHERE row.id IS NOT NULL AND row.classifierId IS NOT NULL
MATCH (c:Classifier {id: row.classifierId})
MATCH (a:Attribute {id: row.id})
MERGE (c)-[:HAS_ATTRIBUTE]->(a);

// Lê methods.csv. Cria relacionamentos HAS_METHOD (Classifier -> Method) usando classifierId.
// Linhas cujo classificador ou método não existe são descartadas pelo MATCH. Sem conversão de tipos.
LOAD CSV WITH HEADERS FROM 'file:///methods.csv' AS row
WITH row WHERE row.id IS NOT NULL AND row.classifierId IS NOT NULL
MATCH (c:Classifier {id: row.classifierId})
MATCH (m:Method {id: row.id})
MERGE (c)-[:HAS_METHOD]->(m);

// Lê relationships.csv. Cria relacionamentos EXTENDS entre Classifier (filho -> pai), filtrando type = 'EXTENDS'.
// Linhas cuja origem ou destino não existe são descartadas pelo MATCH. Sem conversão de tipos.
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'EXTENDS'
MATCH (a:Classifier {id: row.sourceId})
MATCH (b:Classifier {id: row.targetId})
MERGE (a)-[:EXTENDS]->(b);

// Lê relationships.csv. Cria relacionamentos IMPLEMENTS entre Classifier (classe -> interface), filtrando type = 'IMPLEMENTS'.
// Linhas cuja origem ou destino não existe são descartadas pelo MATCH. Sem conversão de tipos.
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'IMPLEMENTS'
MATCH (a:Classifier {id: row.sourceId})
MATCH (b:Classifier {id: row.targetId})
MERGE (a)-[:IMPLEMENTS]->(b);

// Lê relationships.csv. Cria relacionamentos DEPENDS_ON entre Classifier (cliente -> fornecedor), filtrando type = 'DEPENDS_ON'.
// Linhas cuja origem ou destino não existe são descartadas pelo MATCH. Sem conversão de tipos.
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'DEPENDS_ON'
MATCH (a:Classifier {id: row.sourceId})
MATCH (b:Classifier {id: row.targetId})
MERGE (a)-[:DEPENDS_ON]->(b);

// Lê relationships.csv. Cria relacionamentos ASSOCIATES entre Classifier (origem -> destino), filtrando type = 'ASSOCIATES'.
// Grava role e multiplicity como texto (sem conversão). Linhas cuja origem ou destino não existe são descartadas pelo MATCH.
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'ASSOCIATES'
MATCH (a:Classifier {id: row.sourceId})
MATCH (b:Classifier {id: row.targetId})
MERGE (a)-[r:ASSOCIATES]->(b)
SET r.role = row.role,
    r.multiplicity = row.multiplicity;

// Lê relationships.csv. Cria relacionamentos COMPOSED_OF entre Classifier (todo -> parte), filtrando type = 'COMPOSED_OF'.
// Grava role e multiplicity como texto (sem conversão). Linhas cuja origem ou destino não existe são descartadas pelo MATCH.
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'COMPOSED_OF'
MATCH (a:Classifier {id: row.sourceId})
MATCH (b:Classifier {id: row.targetId})
MERGE (a)-[r:COMPOSED_OF]->(b)
SET r.role = row.role,
    r.multiplicity = row.multiplicity;

// Lê relationships.csv. Cria relacionamentos AGGREGATES entre Classifier (todo -> parte), filtrando type = 'AGGREGATES'.
// Grava role e multiplicity como texto (sem conversão). Linhas cuja origem ou destino não existe são descartadas pelo MATCH.
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'AGGREGATES'
MATCH (a:Classifier {id: row.sourceId})
MATCH (b:Classifier {id: row.targetId})
MERGE (a)-[r:AGGREGATES]->(b)
SET r.role = row.role,
    r.multiplicity = row.multiplicity;

// Lê calls.csv. Cria relacionamentos CALLS entre Method (chamador -> chamado).
// Conversão: sequence (texto) -> inteiro com toIntegerOrNull; valor vazio ou inválido vira nulo.
// Linhas cujo chamador ou chamado não existe são descartadas pelo MATCH.
LOAD CSV WITH HEADERS FROM 'file:///calls.csv' AS row
WITH row WHERE row.callerId IS NOT NULL AND row.calleeId IS NOT NULL
MATCH (a:Method {id: row.callerId})
MATCH (b:Method {id: row.calleeId})
MERGE (a)-[r:CALLS]->(b)
SET r.sequence = toIntegerOrNull(row.sequence);
