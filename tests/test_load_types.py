"""Property 3: conversão de tipos nunca grava texto em propriedade booleana ou inteira.

Feature: neo4j-uml-graph-portfolio, Property 3
**Validates: Requirements 7.3, 7.4**

Gera valores variados para as colunas booleanas (isAbstract, isStatic) e inteiras
(position, sequence), executa 01_constraints + 02_load e verifica que, no grafo, as
propriedades são Boolean-or-null e Integer-or-null, nunca texto.
Requer Docker; sem ele a fixture `neo4j_db` ignora os testes.
"""

from __future__ import annotations

import csv
import io

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

pytestmark = pytest.mark.neo4j

# Valores de coluna: booleanos em várias grafias, vazio, espaços, decimais, texto,
# números grandes (inclusive acima de 64 bits) e negativos.
column_values = st.one_of(
    st.sampled_from(
        [
            "true", "TRUE", "True", "false", "FALSE", "1", "0", "",
            " ", "   ", "1.5", "-1.5", "abc", "sim", "yes",
            "-1", "-42", "2147483648", "9223372036854775807",
            "9223372036854775808", "99999999999999999999999", "-99999999999999999999999",
        ]
    ),
    st.integers(min_value=-(10**25), max_value=10**25).map(str),
    st.text(max_size=8).filter(lambda s: "\x00" not in s and "\r" not in s and "\n" not in s),
)


def _csv(header: list[str], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def _write(db, name: str, content: str) -> None:
    path = db.import_dir / name
    path.write_text(content, encoding="utf-8", newline="")
    path.chmod(0o644)


def _write_dataset(db, abstract, static_a, pos_a, static_m, abstract_m, pos_m, seq) -> None:
    _write(db, "classifiers.csv", _csv(
        ["id", "name", "kind", "isAbstract", "package"],
        [["c1", "A", "class", abstract, "domain"], ["c2", "B", "interface", abstract, "domain"]],
    ))
    _write(db, "relationships.csv", _csv(
        ["sourceId", "targetId", "type", "role", "multiplicity"], [["c1", "c2", "IMPLEMENTS", "", ""]],
    ))
    _write(db, "attributes.csv", _csv(
        ["id", "classifierId", "name", "dataType", "visibility", "isStatic", "position"],
        [["a1", "c1", "x", "int", "private", static_a, pos_a]],
    ))
    _write(db, "methods.csv", _csv(
        ["id", "classifierId", "name", "returnType", "visibility", "isStatic", "isAbstract", "position"],
        [
            ["m1", "c1", "f", "void", "public", static_m, abstract_m, pos_m],
            ["m2", "c2", "g", "void", "public", static_m, abstract_m, pos_m],
        ],
    ))
    _write(db, "calls.csv", _csv(["callerId", "calleeId", "sequence"], [["m1", "m2", seq]]))


def _is_bool_or_null(v) -> bool:
    return v is None or type(v) is bool


def _is_int_or_null(v) -> bool:
    return v is None or (type(v) is int and not isinstance(v, bool))


@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    abstract=column_values,
    static_a=column_values,
    pos_a=column_values,
    static_m=column_values,
    abstract_m=column_values,
    pos_m=column_values,
    seq=column_values,
)
def test_property_3_type_conversion_never_stores_text(
    neo4j_db, abstract, static_a, pos_a, static_m, abstract_m, pos_m, seq
):
    # Feature: neo4j-uml-graph-portfolio, Property 3
    db = neo4j_db
    db.reset()
    _write_dataset(db, abstract, static_a, pos_a, static_m, abstract_m, pos_m, seq)
    db.run_script("01_constraints.cypher")
    db.run_script("02_load.cypher")

    classifiers = db.run("MATCH (c:Classifier) RETURN c.isAbstract AS v")
    attributes = db.run("MATCH (a:Attribute) RETURN a.isStatic AS s, a.position AS p")
    methods = db.run(
        "MATCH (m:Method) RETURN m.isStatic AS s, m.isAbstract AS a, m.position AS p"
    )
    calls = db.run("MATCH (:Method)-[r:CALLS]->(:Method) RETURN r.sequence AS q")

    # os nós e a chamada existem: valor inválido vira nulo, não derruba a linha
    assert len(classifiers) == 2 and len(attributes) == 1
    assert len(methods) == 2 and len(calls) == 1

    assert all(_is_bool_or_null(r["v"]) for r in classifiers)
    assert all(_is_bool_or_null(r["s"]) and _is_int_or_null(r["p"]) for r in attributes)
    assert all(
        _is_bool_or_null(r["s"]) and _is_bool_or_null(r["a"]) and _is_int_or_null(r["p"])
        for r in methods
    )
    assert all(_is_int_or_null(r["q"]) for r in calls)


def test_property_3_known_values(neo4j_db):
    """Exemplos fixos: válidos viram o tipo certo; inválidos viram nulo; decimal é truncado."""
    db = neo4j_db
    db.reset()
    _write_dataset(db, "TRUE", "true", "-7", "", "abc", "1.5", "  ")
    db.run_script("01_constraints.cypher")
    db.run_script("02_load.cypher")

    assert db.run("MATCH (c:Classifier {id:'c1'}) RETURN c.isAbstract AS v")[0]["v"] is True
    a = db.run("MATCH (a:Attribute) RETURN a.isStatic AS s, a.position AS p")[0]
    assert a["s"] is True and a["p"] == -7
    m = db.run("MATCH (m:Method {id:'m1'}) RETURN m.isStatic AS s, m.isAbstract AS a, m.position AS p")[0]
    # toIntegerOrNull("1.5") trunca para 1 no Neo4j (decimal não vira nulo); o essencial é ser inteiro
    assert m["s"] is None and m["a"] is None and m["p"] == 1
    assert db.run("MATCH ()-[r:CALLS]->() RETURN r.sequence AS q")[0]["q"] is None
