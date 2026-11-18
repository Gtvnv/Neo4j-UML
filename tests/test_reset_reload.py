"""Property 6: Reset seguido de nova carga reproduz o estado (exige Docker)."""

import pytest
from hypothesis import HealthCheck, given, settings

from tests.helpers.dataset_model import Dataset
from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import dump_graph

pytestmark = pytest.mark.neo4j

PROJECT_CONSTRAINTS = {
    "package_name_unique",
    "classifier_id_unique",
    "attribute_id_unique",
    "method_id_unique",
}


def _load_and_validate(db) -> list[list[dict]]:
    db.run_script("01_constraints.cypher")
    db.run_script("02_load.cypher")
    return db.run_script("04_validate.cypher")


def _check_reset_and_reload(db) -> None:
    """Carrega, faz reset, confere o vazio, recarrega e compara dump e validação."""
    validate1 = _load_and_validate(db)
    dump1 = dump_graph(db.run)
    assert dump1  # a carga produziu algo para o reset remover

    db.reset()
    assert db.run("MATCH (n) RETURN count(n) AS total")[0]["total"] == 0
    assert db.run("MATCH ()-[r]->() RETURN count(r) AS total")[0]["total"] == 0
    names = {r["name"] for r in db.run("SHOW CONSTRAINTS YIELD name RETURN name")}
    assert not (names & PROJECT_CONSTRAINTS)

    validate2 = _load_and_validate(db)
    dump2 = dump_graph(db.run)
    assert dump2 == dump1
    assert validate2 == validate1


# Feature: neo4j-uml-graph-portfolio, Property 6
# Validates: Requirements 7.9, 10.2
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(ds=valid_datasets())
def test_reset_e_recarga_reproduzem_o_estado(neo4j_db, ds: Dataset):
    try:
        neo4j_db.reset()
        neo4j_db.clear_import()
        neo4j_db.write_dataset(ds)
        _check_reset_and_reload(neo4j_db)
    finally:
        neo4j_db.reset()


# Feature: neo4j-uml-graph-portfolio, Property 6
# Validates: Requirements 7.9, 10.2
def test_reset_e_recarga_do_dataset_real(neo4j_db):
    try:
        neo4j_db.reset()
        neo4j_db.clear_import()
        neo4j_db.copy_real_dataset()
        _check_reset_and_reload(neo4j_db)
    finally:
        neo4j_db.reset()
