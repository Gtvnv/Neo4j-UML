"""Property 10: implementadores concretos incluem herança e excluem abstratos e interfaces (Q02)."""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import concrete_implementers

pytestmark = pytest.mark.neo4j


def _expected(ds, interface_name: str) -> set[str]:
    """Oráculo em nomes. Q02 só parte de um nó :Interface; sem ele o resultado é vazio."""
    rows = ds.classifiers.rows
    name_of = {r["id"]: r["name"] for r in rows}
    interfaces = {r["name"] for r in rows if r["kind"] == "interface"}
    if interface_name not in interfaces:
        return set()
    abstract = {r["name"] for r in rows if r["isAbstract"].strip().lower() == "true"}

    def edges(tipo):
        return [
            (name_of[r["sourceId"]], name_of[r["targetId"]])
            for r in ds.relationships.rows
            if r["type"] == tipo
        ]

    return concrete_implementers(
        edges("IMPLEMENTS"), edges("EXTENDS"), interface_name,
        abstract=abstract, interfaces=interfaces,
    )


# Feature: neo4j-uml-graph-portfolio, Property 10
# Validates: Requirements 9.3
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.data())
def test_q02_implementadores_concretos(neo4j_db, data):
    ds = data.draw(valid_datasets())
    names = [r["name"] for r in ds.classifiers.rows]
    interface_names = [r["name"] for r in ds.classifiers.rows if r["kind"] == "interface"]
    # prefere interfaces, mas também sorteia qualquer nome (inclui não-interface)
    alvo = data.draw(st.sampled_from(interface_names or names))
    outro = data.draw(st.sampled_from(names))
    try:
        neo4j_db.reset()
        neo4j_db.clear_import()
        neo4j_db.write_dataset(ds)
        neo4j_db.run_script("01_constraints.cypher")
        neo4j_db.run_script("02_load.cypher")

        for nome in {alvo, outro}:
            rows = neo4j_db.run_query("Q02", interface=nome)
            got = [r["implementacaoConcreta"] for r in rows]
            assert len(got) == len(set(got))  # sem repetição
            assert set(got) == _expected(ds, nome)
    finally:
        neo4j_db.reset()
