"""Property 12: O esquema observado está contido no Modelo_Grafo documentado.

Exige Docker; sem ele os testes são ignorados.
"""

import re
from pathlib import Path

import pytest
from hypothesis import given

from helpers.generators import valid_datasets

pytestmark = pytest.mark.neo4j

DOC_PATH = Path(__file__).resolve().parents[1] / "docs" / "modelo-grafo.md"

PASCAL_CASE = re.compile(r"^[A-Z][a-z0-9]*([A-Z][a-z0-9]*)*$")
UPPER_SNAKE_CASE = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$")
CAMEL_CASE = re.compile(r"^[a-z][a-z0-9]*([A-Z][a-z0-9]*)*$")

_BACKTICKED = re.compile(r"`(\w+)`")
_PROP = re.compile(r"`(\w+)`\s*\(")


# --------------------------------------------------------------------------- parser

def _section(text: str, title: str) -> str:
    match = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    assert match, f"Seção '{title}' não encontrada em modelo-grafo.md"
    return match.group(1)


def _table_rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows[1:]  # descarta o cabeçalho


def parse_model(text: str) -> dict:
    """Extrai labels, tipos de relacionamento e propriedades de docs/modelo-grafo.md."""
    node_props: dict[str, set[str]] = {}
    for cells in _table_rows(_section(text, "Nós")):
        label = _BACKTICKED.search(cells[0]).group(1)
        node_props[label] = set(_PROP.findall(cells[3]))
    rel_props: dict[str, set[str]] = {}
    for cells in _table_rows(_section(text, "Relacionamentos")):
        rel_type = _BACKTICKED.search(cells[0]).group(1)
        rel_props[rel_type] = set(_PROP.findall(cells[4]))
    return {"nodes": node_props, "rels": rel_props}


MODEL = parse_model(DOC_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- observado

def _observed_schema(db) -> tuple[dict[tuple[str, ...], set[str]], dict[str, set[str]]]:
    nodes: dict[tuple[str, ...], set[str]] = {}
    for row in db.run("CALL db.schema.nodeTypeProperties()"):
        key = tuple(sorted(row["nodeLabels"]))
        props = nodes.setdefault(key, set())
        if row["propertyName"] is not None:
            props.add(row["propertyName"])
    rels: dict[str, set[str]] = {}
    for row in db.run("CALL db.schema.relTypeProperties()"):
        rel_type = row["relType"].strip(":`")
        props = rels.setdefault(rel_type, set())
        if row["propertyName"] is not None:
            props.add(row["propertyName"])
    return nodes, rels


def _assert_contained(db) -> None:
    nodes, rels = _observed_schema(db)
    doc_nodes, doc_rels = MODEL["nodes"], MODEL["rels"]
    for labels, props in nodes.items():
        for label in labels:
            assert label in doc_nodes, f"Label não documentado: {label}"
            assert PASCAL_CASE.match(label), f"Label fora de PascalCase: {label}"
        allowed = set().union(*(doc_nodes[label] for label in labels))
        extra = props - allowed
        assert not extra, f"Propriedades não documentadas em {labels}: {extra}"
        for prop in props:
            assert CAMEL_CASE.match(prop), f"Propriedade fora de camelCase: {prop}"
    for rel_type, props in rels.items():
        assert rel_type in doc_rels, f"Tipo de relacionamento não documentado: {rel_type}"
        assert UPPER_SNAKE_CASE.match(rel_type), f"Tipo fora de UPPER_SNAKE_CASE: {rel_type}"
        extra = props - doc_rels[rel_type]
        assert not extra, f"Propriedades não documentadas em {rel_type}: {extra}"
        for prop in props:
            assert CAMEL_CASE.match(prop), f"Propriedade fora de camelCase: {prop}"


# --------------------------------------------------------------------------- testes

def test_documento_segue_convencoes_de_nomes():
    """O próprio documento usa PascalCase, UPPER_SNAKE_CASE e camelCase."""
    assert MODEL["nodes"] and MODEL["rels"]
    for label, props in MODEL["nodes"].items():
        assert PASCAL_CASE.match(label), label
        assert all(CAMEL_CASE.match(p) for p in props), (label, props)
    for rel_type, props in MODEL["rels"].items():
        assert UPPER_SNAKE_CASE.match(rel_type), rel_type
        assert all(CAMEL_CASE.match(p) for p in props), (rel_type, props)


# Feature: neo4j-uml-graph-portfolio, Property 12
# **Validates: Requirements 8.1, 8.2, 8.8**
@given(ds=valid_datasets())
def test_esquema_observado_esta_contido_no_documentado(neo4j_db, ds):
    neo4j_db.reset()
    neo4j_db.clear_import()
    neo4j_db.write_dataset(ds)
    neo4j_db.run_script("01_constraints.cypher")
    neo4j_db.run_script("02_load.cypher")
    _assert_contained(neo4j_db)


# Feature: neo4j-uml-graph-portfolio, Property 12
# **Validates: Requirements 8.1, 8.2, 8.8**
def test_esquema_do_dataset_real_esta_contido_no_documentado(neo4j_db):
    neo4j_db.reset()
    neo4j_db.clear_import()
    neo4j_db.copy_real_dataset()
    neo4j_db.run_script("01_constraints.cypher")
    neo4j_db.run_script("02_load.cypher")
    _assert_contained(neo4j_db)
    neo4j_db.reset()
