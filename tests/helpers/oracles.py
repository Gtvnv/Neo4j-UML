"""Oráculos em Python: contagens esperadas a partir dos CSVs e dump ordenado do grafo.

Regras que espelham o comportamento do Script_Carga:
- campo CSV vazio é lido como nulo pelo LOAD CSV, e linhas com chave nula são descartadas;
- MERGE por chave deduplica nós e relacionamentos repetidos;
- MATCH de extremo inexistente descarta a linha do relacionamento.
Contagens zero são omitidas, como no resultado do 04_validate.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Callable, Iterable

from .dataset_model import Dataset

UML_TYPES = ("EXTENDS", "IMPLEMENTS", "DEPENDS_ON", "ASSOCIATES", "COMPOSED_OF", "AGGREGATES")
KIND_LABELS = {"class": "Class", "interface": "Interface", "enum": "Enum"}

RunQuery = Callable[[str], list[dict[str, Any]]]


def _ids(rows: Iterable[dict[str, str]], column: str = "id") -> set[str]:
    return {r[column] for r in rows if r.get(column)}


def expected_node_counts(ds: Dataset) -> dict[str, int]:
    """Contagem esperada de nós por label (inclui os labels secundários de Classifier)."""
    counts: Counter[str] = Counter()
    counts["Package"] = len({r["package"] for r in ds.classifiers.rows if r.get("package")})

    kinds: dict[str, str] = {}
    for r in ds.classifiers.rows:
        if r.get("id"):
            kinds[r["id"]] = r.get("kind", "")  # SET: a última linha do mesmo id prevalece
    counts["Classifier"] = len(kinds)
    for kind in kinds.values():
        label = KIND_LABELS.get(kind)
        if label:
            counts[label] += 1

    counts["Attribute"] = len(_ids(ds.attributes.rows))
    counts["Method"] = len(_ids(ds.methods.rows))
    return {k: v for k, v in counts.items() if v}


def expected_relationship_counts(ds: Dataset) -> dict[str, int]:
    """Contagem esperada de relacionamentos por tipo."""
    classifiers = _ids(ds.classifiers.rows)
    attributes = _ids(ds.attributes.rows)
    methods = _ids(ds.methods.rows)
    counts: dict[str, int] = {}

    contains = {
        (r["package"], r["id"])
        for r in ds.classifiers.rows
        if r.get("id") and r.get("package")
    }
    counts["CONTAINS"] = len(contains)

    counts["HAS_ATTRIBUTE"] = len({
        (r["classifierId"], r["id"])
        for r in ds.attributes.rows
        if r.get("id") and r.get("classifierId") in classifiers and r["id"] in attributes
    })
    counts["HAS_METHOD"] = len({
        (r["classifierId"], r["id"])
        for r in ds.methods.rows
        if r.get("id") and r.get("classifierId") in classifiers and r["id"] in methods
    })

    for tipo in UML_TYPES:
        counts[tipo] = len({
            (r["sourceId"], r["targetId"])
            for r in ds.relationships.rows
            if r.get("type") == tipo
            and r.get("sourceId") in classifiers
            and r.get("targetId") in classifiers
        })

    counts["CALLS"] = len({
        (r["callerId"], r["calleeId"])
        for r in ds.calls.rows
        if r.get("callerId") in methods and r.get("calleeId") in methods
    })
    return {k: v for k, v in counts.items() if v}


def counts_from_rows(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Converte linhas do 04_validate (`label`/`tipo` e `total`) em dicionário sem zeros."""
    return {r[key]: int(r["total"]) for r in rows if int(r["total"])}


def _node_key(labels: list[str], props: dict[str, Any]) -> str:
    ident = props.get("id", props.get("name"))
    return f"{'|'.join(sorted(labels))}:{ident}"


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)


def dump_graph(run: RunQuery) -> dict[str, list[dict[str, Any]]]:
    """Dump ordenado de nós e relacionamentos com propriedades, sem ids internos do banco.

    `run` executa uma consulta Cypher e devolve uma lista de dicionários.
    Dois grafos equivalentes produzem dumps iguais.
    """
    nodes = [
        {"labels": sorted(r["labels"]), "properties": dict(r["props"])}
        for r in run("MATCH (n) RETURN labels(n) AS labels, properties(n) AS props")
    ]
    rels = [
        {
            "start": _node_key(r["sl"], r["sp"]),
            "type": r["type"],
            "end": _node_key(r["el"], r["ep"]),
            "properties": dict(r["props"]),
        }
        for r in run(
            "MATCH (a)-[r]->(b) RETURN labels(a) AS sl, properties(a) AS sp, type(r) AS type, "
            "properties(r) AS props, labels(b) AS el, properties(b) AS ep"
        )
    ]
    return {
        "nodes": sorted(nodes, key=_canon),
        "relationships": sorted(rels, key=_canon),
    }


# --------------------------------------------------------------------------- consultas
# Oráculos puros das consultas Q01 a Q07. Arestas são pares (origem, destino) de
# identificadores; o chamador filtra antes pelo tipo de relacionamento.

Edge = tuple[str, str]

LAYER_FORBIDDEN_TARGETS = ("service", "repository", "infra")


def _adjacency(edges: Iterable[Edge]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for src, dst in edges:
        adj.setdefault(src, set()).add(dst)
    return adj


def transitive_closure(
    edges: Iterable[Edge], start: str, max_depth: int | None = None
) -> set[str]:
    """Nós alcançáveis a partir de `start` por 1 ou mais arestas (busca em largura).

    `max_depth` limita o número de arestas do caminho. `start` só entra no resultado
    se estiver em um ciclo (alcançável por pelo menos uma aresta), como em `*1..`.
    """
    adj = _adjacency(edges)
    dist: dict[str, int] = {}
    frontier = [start]
    depth = 0
    while frontier and (max_depth is None or depth < max_depth):
        depth += 1
        nxt: list[str] = []
        for node in frontier:
            for nb in adj.get(node, ()):
                if nb not in dist:
                    dist[nb] = depth
                    nxt.append(nb)
        frontier = nxt
    return set(dist)


def simple_cycles(
    edges: Iterable[Edge], min_len: int = 2, max_len: int = 5
) -> list[tuple[str, ...]]:
    """Ciclos simples (nós distintos) de `min_len` a `max_len` nós.

    Cada ciclo sai uma vez, como tupla de ids iniciando pelo menor id (rotação normalizada).
    A lista é ordenada.
    """
    adj = _adjacency(edges)
    found: set[tuple[str, ...]] = set()

    def walk(start: str, path: list[str]) -> None:
        for nb in adj.get(path[-1], ()):
            if nb == start and len(path) >= min_len:
                found.add(tuple(path))
            elif nb > start and nb not in path and len(path) < max_len:
                path.append(nb)
                walk(start, path)
                path.pop()

    for s in sorted(adj):
        walk(s, [s])
    return sorted(found)


def layer_violations(
    edges: Iterable[Edge],
    package_of: dict[str, str],
    source_package: str = "domain",
    forbidden: Iterable[str] = LAYER_FORBIDDEN_TARGETS,
) -> list[tuple[str, str, str]]:
    """Dependências de `source_package` para pacotes proibidos.

    Devolve (origem, destino, pacote do destino), ordenado por origem e destino.
    """
    bad = set(forbidden)
    return sorted(
        {
            (s, t, package_of[t])
            for s, t in edges
            if package_of.get(s) == source_package and package_of.get(t) in bad
        },
        key=lambda x: (x[0], x[1]),
    )


def coupling_degrees(
    names: Iterable[str], edges: Iterable[Edge]
) -> list[tuple[str, int, int, int]]:
    """Grau de entrada, saída e total por nome, ordenado por total desc e nome asc.

    Cada aresta conta uma vez (laço próprio conta como entrada e saída, como no Cypher).
    Devolve tuplas (nome, entrada, saida, total).
    """
    entrada: Counter[str] = Counter()
    saida: Counter[str] = Counter()
    for s, t in edges:
        saida[s] += 1
        entrada[t] += 1
    rows = [(n, entrada[n], saida[n], entrada[n] + saida[n]) for n in set(names)]
    return sorted(rows, key=lambda r: (-r[3], r[0]))


def concrete_implementers(
    implements: Iterable[Edge],
    extends: Iterable[Edge],
    interface: str,
    abstract: Iterable[str] = (),
    interfaces: Iterable[str] = (),
) -> set[str]:
    """Classes concretas que implementam `interface` direta ou por herança (EXTENDS*0..).

    `implements` e `extends` são pares (origem, destino). Exclui interfaces e abstratos.
    """
    direct = {s for s, t in implements if t == interface}
    down = [(t, s) for s, t in extends]  # ancestral -> descendente
    result = set(direct)  # profundidade 0
    for d in direct:
        result |= transitive_closure(down, d)
    return result - set(abstract) - set(interfaces)
