"""Testes puros do divisor de instruções Cypher e dos oráculos de contagem."""

from helpers.dataset_model import Dataset
from helpers.neo4j_fixture import CYPHER_DIR, split_statements
from helpers.oracles import expected_node_counts, expected_relationship_counts


def test_splits_on_semicolon():
    assert split_statements("RETURN 1; RETURN 2;") == ["RETURN 1", "RETURN 2"]


def test_ignores_semicolon_in_comments_and_literals():
    text = (
        "// comentário; com ponto e vírgula\n"
        "RETURN 'a;b' AS x; /* bloco; ainda bloco */\n"
        'RETURN "c;d" AS y, `e;f` AS z, \'it\\\'s;\' AS w;\n'
    )
    assert split_statements(text) == [
        "RETURN 'a;b' AS x",
        'RETURN "c;d" AS y, `e;f` AS z, \'it\\\'s;\' AS w',
    ]


def test_keeps_comment_marker_inside_literal_and_drops_comment_only_statements():
    assert split_statements("RETURN 'http://x' AS u; // só comentário\n;") == [
        "RETURN 'http://x' AS u"
    ]


def test_real_scripts_statement_counts():
    load = (CYPHER_DIR / "02_load.cypher").read_text(encoding="utf-8")
    assert len(split_statements(load)) == 14
    constraints = (CYPHER_DIR / "01_constraints.cypher").read_text(encoding="utf-8")
    assert len(split_statements(constraints)) == 4


def test_oracle_counts_small_dataset():
    ds = Dataset.empty()
    ds.classifiers.add(id="A", name="A", kind="class", isAbstract="false", package="p")
    ds.classifiers.add(id="I", name="I", kind="interface", isAbstract="", package="p")
    ds.relationships.add(sourceId="A", targetId="I", type="IMPLEMENTS")
    ds.relationships.add(sourceId="A", targetId="X", type="EXTENDS")  # extremo inexistente
    assert expected_node_counts(ds) == {
        "Package": 1, "Classifier": 2, "Class": 1, "Interface": 1,
    }
    assert expected_relationship_counts(ds) == {"CONTAINS": 2, "IMPLEMENTS": 1}
