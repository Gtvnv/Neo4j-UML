"""Property 4: A carga é idempotente (exige Docker; sem ele os testes são ignorados)."""

import pytest
from hypothesis import given

from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import dump_graph, expected_node_counts, expected_relationship_counts

pytestmark = pytest.mark.neo4j

NODE_COUNT_QUERY = "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS total"
REL_COUNT_QUERY = "MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total"


def _counts(db) -> tuple[dict[str, int], dict[str, int]]:
    nodes = {r["label"]: r["total"] for r in db.run(NODE_COUNT_QUERY)}
    rels = {r["tipo"]: r["total"] for r in db.run(REL_COUNT_QUERY)}
    return nodes, rels


def _load_twice_and_compare(db) -> tuple[dict[str, int], dict[str, int]]:
    db.run_script("01_constraints.cypher")
    db.run_script("02_load.cypher")
    dump1 = dump_graph(db.run)
    counts1 = _counts(db)

    db.run_script("02_load.cypher")
    dump2 = dump_graph(db.run)
    counts2 = _counts(db)

    assert dump2 == dump1
    assert counts2 == counts1
    return counts1


# Feature: neo4j-uml-graph-portfolio, Property 4
# **Validates: Requirements 7.7**
@given(ds=valid_datasets())
def test_carga_e_idempotente(neo4j_db, ds):
    neo4j_db.reset()
    neo4j_db.clear_import()
    neo4j_db.write_dataset(ds)
    nodes, rels = _load_twice_and_compare(neo4j_db)
    assert nodes == expected_node_counts(ds)
    assert rels == expected_relationship_counts(ds)


# Feature: neo4j-uml-graph-portfolio, Property 4
# **Validates: Requirements 7.7**
def test_carga_do_dataset_real_e_idempotente(neo4j_db):
    neo4j_db.reset()
    neo4j_db.clear_import()
    neo4j_db.copy_real_dataset()
    _load_twice_and_compare(neo4j_db)
    neo4j_db.reset()
