// Script de reset (destrutivo, restrito aos labels do projeto).
// Volta o banco ao estado vazio para permitir repetir 01_constraints, 02_load e 04_validate.

// Estágio 1: remove nós do projeto e seus relacionamentos.
MATCH (n) WHERE n:Package OR n:Classifier OR n:Attribute OR n:Method
DETACH DELETE n;

// Estágio 2: remove as constraints do projeto.
DROP CONSTRAINT package_name_unique IF EXISTS;
DROP CONSTRAINT classifier_id_unique IF EXISTS;
DROP CONSTRAINT attribute_id_unique IF EXISTS;
DROP CONSTRAINT method_id_unique IF EXISTS;
