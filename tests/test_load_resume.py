"""Propriedade 5: retomar uma carga interrompida converge para o mesmo grafo.

Feature: neo4j-uml-graph-portfolio, Property 5: Retomar uma carga interrompida converge para o mesmo grafo

**Validates: Requirements 7.8**

Sem Docker, os testes são ignorados pela fixture `neo4j_db`.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tests.helpers.generators import valid_datasets
from tests.helpers.oracles import dump_graph

pytestmark = pytest.mark.neo4j

TOTAL_STATEMENTS = 14


def _fresh_load(db, ds):
    db.reset()
    db.write_dataset(ds)
    db.run_script("01_constraints.cypher")


@settings(max_examples=15, deadline=None)
@given(ds=valid_datasets(), prefix=st.integers(0, TOTAL_STATEMENTS))
def test_resume_after_partial_load_equals_clean_load(neo4j_db, ds, prefix):
    # Feature: neo4j-uml-graph-portfolio, Property 5
    # carga limpa de referência
    _fresh_load(neo4j_db, ds)
    neo4j_db.run_script("02_load.cypher")
    expected = dump_graph(neo4j_db.run)

    # carga interrompida após `prefix` instruções, seguida da carga completa sem reset
    _fresh_load(neo4j_db, ds)
    neo4j_db.run_script("02_load.cypher", limit=prefix)
    neo4j_db.run_script("02_load.cypher")
    actual = dump_graph(neo4j_db.run)

    assert actual == expected


def test_load_script_has_expected_statement_count():
    """Garante que o intervalo 0..14 do teste cobre todas as instruções do 02_load."""
    from tests.helpers.neo4j_fixture import CYPHER_DIR, split_statements

    text = (CYPHER_DIR / "02_load.cypher").read_text(encoding="utf-8")
    assert len(split_statements(text)) == TOTAL_STATEMENTS
