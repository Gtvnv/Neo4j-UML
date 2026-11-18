"""Testes de exemplo dos scripts de constraints e carga (Requirements 5.10, 6.1-6.4, 6.6, 7.6).

Os testes de texto rodam sem banco. Os que usam `neo4j_db` exigem Docker e são ignorados sem ele.
"""

import re
import time
from pathlib import Path

import pytest

CYPHER_DIR = Path(__file__).resolve().parent.parent / "cypher"
CONSTRAINT_NAMES = {
    "package_name_unique",
    "classifier_id_unique",
    "attribute_id_unique",
    "method_id_unique",
}
LOAD_TIME_LIMIT_SECONDS = 30


def _lines(name: str) -> list[str]:
    return (CYPHER_DIR / name).read_text(encoding="utf-8").splitlines()


def _previous_line_is_comment(lines: list[str], index: int) -> bool:
    """A linha imediatamente anterior (sem linha em branco no meio) é um comentário `//`."""
    return index > 0 and lines[index - 1].strip().startswith("//")


# ----------------------------------------------------------------- testes de texto

def test_constraints_sao_exatamente_quatro_com_if_not_exists_e_comentario():
    lines = _lines("01_constraints.cypher")
    indices = [i for i, ln in enumerate(lines) if re.match(r"\s*CREATE\s+CONSTRAINT\b", ln, re.I)]
    assert len(indices) == 4
    names = set()
    for i in indices:
        assert re.search(r"\bIF\s+NOT\s+EXISTS\b", lines[i], re.I), f"linha {i + 1} sem IF NOT EXISTS"
        assert _previous_line_is_comment(lines, i), f"linha {i + 1} sem comentário imediatamente antes"
        names.add(re.search(r"CONSTRAINT\s+(\w+)", lines[i], re.I).group(1))
    assert names == CONSTRAINT_NAMES


def test_todo_load_csv_e_precedido_de_comentario():
    lines = _lines("02_load.cypher")
    indices = [i for i, ln in enumerate(lines) if re.match(r"\s*LOAD\s+CSV\b", ln, re.I)]
    assert indices, "nenhum LOAD CSV encontrado"
    for i in indices:
        assert _previous_line_is_comment(lines, i), f"LOAD CSV na linha {i + 1} sem comentário antes"


# ----------------------------------------------------------------- testes com banco

def _catalog(db) -> list[tuple]:
    rows = db.run(
        "SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties "
        "RETURN name, type, labelsOrTypes, properties ORDER BY name"
    )
    return [(r["name"], r["type"], tuple(r["labelsOrTypes"]), tuple(r["properties"])) for r in rows]


@pytest.mark.neo4j
def test_constraints_duas_execucoes_sem_erro_e_mesmo_catalogo(neo4j_db):
    neo4j_db.reset()
    neo4j_db.run_script("01_constraints.cypher")
    first = _catalog(neo4j_db)
    neo4j_db.run_script("01_constraints.cypher")
    second = _catalog(neo4j_db)
    assert {c[0] for c in first} == CONSTRAINT_NAMES
    assert second == first
    neo4j_db.reset()


@pytest.mark.neo4j
def test_id_duplicado_e_rejeitado_e_no_original_e_preservado(neo4j_db):
    from neo4j.exceptions import ConstraintError

    neo4j_db.reset()
    neo4j_db.clear_import()
    neo4j_db.copy_real_dataset()
    neo4j_db.run_script("01_constraints.cypher")
    neo4j_db.run_script("02_load.cypher")

    original = neo4j_db.run("MATCH (c:Classifier) RETURN c.id AS id, c.name AS name ORDER BY id LIMIT 1")[0]
    before = neo4j_db.run("MATCH (c:Classifier) RETURN count(c) AS total")[0]["total"]

    with pytest.raises(ConstraintError):
        neo4j_db.run("CREATE (:Classifier {id: $id, name: 'Duplicado'})", id=original["id"])

    after = neo4j_db.run("MATCH (c:Classifier) RETURN count(c) AS total")[0]["total"]
    kept = neo4j_db.run("MATCH (c:Classifier {id: $id}) RETURN c.name AS name", id=original["id"])
    assert after == before
    assert [r["name"] for r in kept] == [original["name"]]
    neo4j_db.reset()


@pytest.mark.neo4j
def test_carga_do_dataset_real_em_ate_30_segundos(neo4j_db):
    neo4j_db.reset()
    neo4j_db.clear_import()
    neo4j_db.copy_real_dataset()
    start = time.perf_counter()
    neo4j_db.run_script("01_constraints.cypher")
    neo4j_db.run_script("02_load.cypher")
    elapsed = time.perf_counter() - start
    neo4j_db.reset()
    assert elapsed <= LOAD_TIME_LIMIT_SECONDS, f"carga levou {elapsed:.1f}s"
