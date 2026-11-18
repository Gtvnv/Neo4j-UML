// Script de validação (somente leitura). Execute logo após a carga (02_load)
// e compare os resultados com a tabela de contagens esperadas do README.

// Contagem de nós por label. Classifier aparece junto com Class, Interface e Enum,
// porque labels(n) devolve todos os labels de cada nó.
MATCH (n) UNWIND labels(n) AS label
RETURN label, count(*) AS total ORDER BY label;

// Contagem de relacionamentos por tipo.
MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total ORDER BY tipo;
