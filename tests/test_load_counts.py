"""Property 2: contagens após a carga são iguais às do oráculo."""

import pytest
from hypothesis import HealthCheck, given, settings

from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import (
    counts_from_rows,
    expected_node_counts,
    expected_relationship_counts,
)

pytestmark = pytest.mark.neo4j


def _load(db, ds) -> list[list[dict]]:
    """Banco vazio -> 01_constraints -> CSVs -> 02_load. Devolve o resultado do 04_validate."""
    db.reset()
    db.clear_import()
    db.write_dataset(ds)
    db.run_script("01_constraints.cypher")
    db.run_script("02_load.cypher")
    return db.run_script("04_validate.cypher")


# Feature: neo4j-uml-graph-portfolio, Property 2
# Validates: Requirements 3.5, 5.2, 7.1, 7.5, 7.10
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(valid_datasets())
def test_contagens_apos_carga_iguais_ao_oraculo(neo4j_db, ds):
    try:
        validate_result = _load(neo4j_db, ds)

        # contagens lidas diretamente do banco
        nodes = counts_from_rows(
            neo4j_db.run("MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS total"),
            "label",
        )
        rels = counts_from_rows(
            neo4j_db.run("MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total"), "tipo"
        )
        assert nodes == expected_node_counts(ds)
        assert rels == expected_relationship_counts(ds)

        # resultado do 04_validate (duas consultas: labels e tipos)
        assert len(validate_result) == 2
        assert counts_from_rows(validate_result[0], "label") == expected_node_counts(ds)
        assert counts_from_rows(validate_result[1], "tipo") == expected_relationship_counts(ds)
    finally:
        neo4j_db.reset()
