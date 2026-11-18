"""Property 11: acoplamento é entrada, saída e total corretos, na ordem pedida (Q06)."""

import pytest
from hypothesis import HealthCheck, given, settings

from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import UML_TYPES, coupling_degrees

pytestmark = pytest.mark.neo4j


# Feature: neo4j-uml-graph-portfolio, Property 11
# Validates: Requirements 9.7
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(valid_datasets())
def test_acoplamento_entrada_saida_total_na_ordem_pedida(neo4j_db, ds):
    db = neo4j_db
    try:
        db.reset()
        db.clear_import()
        db.write_dataset(ds)
        db.run_script("01_constraints.cypher")
        db.run_script("02_load.cypher")

        name_of = {r["id"]: r["name"] for r in ds.classifiers.rows if r.get("id")}
        # MERGE deduplica por (origem, destino, tipo); extremos inexistentes são descartados
        distinct = {
            (r["sourceId"], r["targetId"], r["type"])
            for r in ds.relationships.rows
            if r.get("type") in UML_TYPES
            and r.get("sourceId") in name_of
            and r.get("targetId") in name_of
        }
        edges = [(name_of[s], name_of[t]) for s, t, _ in distinct]
        expected = coupling_degrees(name_of.values(), edges)

        rows = db.run_query("Q06")
        actual = [(r["classificador"], r["entrada"], r["saida"], r["total"]) for r in rows]
        assert actual == expected
    finally:
        db.reset()
