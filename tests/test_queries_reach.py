"""Property 7: consultas de alcançabilidade (Q01, Q03, Q07) iguais ao fechamento do oráculo."""

import pytest
from hypothesis import HealthCheck, given, settings

from tests.helpers.dataset_model import Dataset
from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import transitive_closure

pytestmark = pytest.mark.neo4j

MAX_DEPTH_Q07 = 10


def _edges(ds: Dataset, tipo: str) -> list[tuple[str, str]]:
    return [(r["sourceId"], r["targetId"]) for r in ds.relationships.rows if r["type"] == tipo]


def _name(cid: str) -> str:
    return f"Name{cid}"


def _check_reach(db, ds: Dataset) -> None:
    db.run_script("01_constraints.cypher")
    db.run_script("02_load.cypher")

    ids = [r["id"] for r in ds.classifiers.rows]

    # Q01: ancestrais por EXTENDS (sem repetição, ordenados)
    extends = _edges(ds, "EXTENDS")
    for cid in ids:
        got = [r["ancestral"] for r in db.run_query("Q01", nome=_name(cid))]
        expected = sorted(_name(x) for x in transitive_closure(extends, cid))
        assert got == expected, f"Q01 {cid}"

    # Q03: impactados por DEPENDS_ON (quem depende, transitivamente), sem o próprio nó
    reverse = [(t, s) for s, t in _edges(ds, "DEPENDS_ON")]
    for cid in ids:
        got = [r["impactado"] for r in db.run_query("Q03", nome=_name(cid))]
        expected = sorted(_name(x) for x in transitive_closure(reverse, cid) - {cid})
        assert got == expected, f"Q03 {cid}"

    # Q07: métodos alcançados por CALLS em até 10 níveis (a consulta casa o método pelo id)
    calls = [(r["callerId"], r["calleeId"]) for r in ds.calls.rows]
    for mid in [r["id"] for r in ds.methods.rows]:
        got = [r["metodoAlcancado"] for r in db.run_query("Q07", metodo=mid)]
        expected = sorted(transitive_closure(calls, mid, max_depth=MAX_DEPTH_Q07))
        assert got == expected, f"Q07 {mid}"


# Feature: neo4j-uml-graph-portfolio, Property 7
# Validates: Requirements 9.2, 9.4, 9.8
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(ds=valid_datasets())
def test_consultas_de_alcancabilidade_igualam_o_fechamento_do_oraculo(neo4j_db, ds: Dataset):
    try:
        neo4j_db.reset()
        neo4j_db.clear_import()
        neo4j_db.write_dataset(ds)
        _check_reach(neo4j_db, ds)
    finally:
        neo4j_db.reset()


# Feature: neo4j-uml-graph-portfolio, Property 7
# Validates: Requirements 9.2, 9.4, 9.8
def test_alcancabilidade_com_ciclo_e_profundidade_maxima(neo4j_db):
    """Ciclo A->B->A em DEPENDS_ON (A impactado por si só é excluído) e cadeia CALLS de 12 níveis."""
    ds = Dataset.empty()
    for cid in ("c0", "c1", "c2"):
        ds.classifiers.add(id=cid, name=_name(cid), kind="class", isAbstract="false", package="domain")
    ds.relationships.add(sourceId="c0", targetId="c1", type="DEPENDS_ON", role="", multiplicity="")
    ds.relationships.add(sourceId="c1", targetId="c0", type="DEPENDS_ON", role="", multiplicity="")
    ds.relationships.add(sourceId="c2", targetId="c0", type="DEPENDS_ON", role="", multiplicity="")
    ds.relationships.add(sourceId="c0", targetId="c1", type="EXTENDS", role="", multiplicity="")
    ds.relationships.add(sourceId="c1", targetId="c0", type="EXTENDS", role="", multiplicity="")
    for i in range(12):
        ds.methods.add(
            id=f"m{i}", classifierId="c0", name=f"met{i}", returnType="void", visibility="public",
            isStatic="false", isAbstract="false", position=str(i),
        )
    for i in range(11):
        ds.calls.add(callerId=f"m{i}", calleeId=f"m{i + 1}", sequence=str(i))
    ds.attributes.add(
        id="a0", classifierId="c0", name="att0", dataType="String", visibility="public",
        isStatic="false", position="0",
    )
    try:
        neo4j_db.reset()
        neo4j_db.clear_import()
        neo4j_db.write_dataset(ds)
        _check_reach(neo4j_db, ds)
        # limite de profundidade: m0 alcança m1..m10, não m11
        got = [r["metodoAlcancado"] for r in neo4j_db.run_query("Q07", metodo="m0")]
        assert "m10" in got and "m11" not in got
    finally:
        neo4j_db.reset()
