"""Testes unitários puros dos oráculos de consultas e do extrator de Qnn."""

from tests.helpers.neo4j_fixture import extract_queries, load_queries, parse_param_defaults
from tests.helpers.oracles import (
    concrete_implementers,
    coupling_degrees,
    layer_violations,
    simple_cycles,
    transitive_closure,
)


def test_closure_with_cycle_and_depth_limit():
    edges = [("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")]
    assert transitive_closure(edges, "a") == {"a", "b", "c", "d"}
    assert transitive_closure(edges, "a", max_depth=2) == {"b", "c"}
    assert transitive_closure(edges, "d") == set()


def test_cycles_normalized_and_bounded():
    edges = [("b", "c"), ("c", "a"), ("a", "b"), ("x", "y"), ("y", "x"), ("z", "z")]
    assert simple_cycles(edges) == [("a", "b", "c"), ("x", "y")]
    long_ring = [(str(i), str((i + 1) % 6)) for i in range(6)]
    assert simple_cycles(long_ring) == []


def test_layer_violations():
    pkg = {"P": "domain", "G": "infra", "O": "domain", "S": "service"}
    edges = [("P", "G"), ("O", "P"), ("S", "G")]
    assert layer_violations(edges, pkg) == [("P", "G", "infra")]


def test_coupling_order_total_desc_then_name():
    rows = coupling_degrees(["A", "B", "C"], [("A", "B"), ("C", "B"), ("A", "C")])
    assert rows == [("A", 0, 2, 2), ("B", 2, 0, 2), ("C", 1, 1, 2)]
    rows = coupling_degrees(["A", "B", "C"], [("A", "B"), ("C", "B")])
    assert [r[0] for r in rows] == ["B", "A", "C"]


def test_concrete_implementers_includes_inheritance():
    implements = [("Base", "I"), ("Abs", "I")]
    extends = [("Child", "Base"), ("GrandChild", "Child")]
    result = concrete_implementers(implements, extends, "I", abstract={"Abs"}, interfaces={"J"})
    assert result == {"Base", "Child", "GrandChild"}


def test_extract_queries_from_text_and_real_file():
    text = ":param n => 'X'\n// Q01 - pergunta\n// nota\nMATCH (a)\nRETURN a;\n"
    assert extract_queries(text) == {"Q01": "MATCH (a)\nRETURN a"}
    assert parse_param_defaults(text) == {"n": "X"}
    assert sorted(load_queries()) == [f"Q0{i}" for i in range(1, 9)]
