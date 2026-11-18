// Garante um único Package por nome.
CREATE CONSTRAINT package_name_unique IF NOT EXISTS
FOR (p:Package) REQUIRE p.name IS UNIQUE;

// Garante um único Classifier por id (a constraint cria também o índice de busca).
CREATE CONSTRAINT classifier_id_unique IF NOT EXISTS
FOR (c:Classifier) REQUIRE c.id IS UNIQUE;

// Garante um único Attribute por id.
CREATE CONSTRAINT attribute_id_unique IF NOT EXISTS
FOR (a:Attribute) REQUIRE a.id IS UNIQUE;

// Garante um único Method por id.
CREATE CONSTRAINT method_id_unique IF NOT EXISTS
FOR (m:Method) REQUIRE m.id IS UNIQUE;
