"""Property 9: violação de camadas é o filtro exato das dependências proibidas."""

import pytest
from hypothesis import HealthCheck, given, settings

from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import layer_violations

pytestmark = pytest.mark.neo4j


def _load(db, ds) -> None:
    """Banco vazio -> 01_constraints -> CSVs -> 02_load."""
    db.reset()
    db.clear_import()
    db.write_dataset(ds)
    db.run_script("01_constraints.cypher")
    db.run_script("02_load.cypher")


# Feature: neo4j-uml-graph-portfolio, Property 9
# Validates: Requirements 5.7, 9.6
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(valid_datasets())
def test_violacao_de_camadas_e_filtro_exato_das_dependencias_proibidas(neo4j_db, ds):
    try:
        _load(neo4j_db, ds)

        name_of = {r["id"]: r["name"] for r in ds.classifiers.rows}
        package_of = {r["name"]: r["package"] for r in ds.classifiers.rows}
        edges = [
            (name_of[r["sourceId"]], name_of[r["targetId"]])
            for r in ds.relationships.rows
            if r["type"] == "DEPENDS_ON"
        ]
        expected = layer_violations(edges, package_of)

        rows = neo4j_db.run_query("Q05")
        actual = [(r["origem"], r["destino"], r["pacoteDestino"]) for r in rows]

        assert sorted(actual) == sorted(expected)
    finally:
        neo4j_db.reset()
