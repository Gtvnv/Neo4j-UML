"""Property 8: detecção de ciclos devolve cada ciclo simples uma única vez."""

import pytest
from hypothesis import HealthCheck, given, settings

from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import simple_cycles

pytestmark = pytest.mark.neo4j


# Feature: neo4j-uml-graph-portfolio, Property 8
# Validates: Requirements 5.6, 9.5
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(valid_datasets())
def test_q04_devolve_cada_ciclo_simples_uma_vez(neo4j_db, ds):
    try:
        neo4j_db.reset()
        neo4j_db.clear_import()
        neo4j_db.write_dataset(ds)
        neo4j_db.run_script("01_constraints.cypher")
        neo4j_db.run_script("02_load.cypher")

        nomes = {r["id"]: r["name"] for r in ds.classifiers.rows}
        arestas = {
            (r["sourceId"], r["targetId"])
            for r in ds.relationships.rows
            if r["type"] == "DEPENDS_ON"
        }
        # oráculo: ciclos como tuplas de ids (rotação pelo menor id), convertidos em nomes
        esperado = sorted(tuple(nomes[i] for i in ciclo) for ciclo in simple_cycles(arestas, 2, 5))

        linhas = neo4j_db.run_query("Q04")
        obtido = sorted(tuple(r["ciclo"]) for r in linhas)

        assert len(obtido) == len(set(obtido)), "ciclo repetido em Q04"
        assert obtido == esperado
        if not esperado:
            assert linhas == []
    finally:
        neo4j_db.reset()
