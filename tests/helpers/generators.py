"""Estratégias Hypothesis: datasets válidos e mutações inválidas (Requirement 5)."""

from __future__ import annotations

import copy

from hypothesis import strategies as st

from .dataset_model import Dataset
from .validator import (
    R_ID_DUPLICADO,
    R_ID_VAZIO,
    R_MAX_LINHAS,
    R_MULTIPLICIDADE,
    R_REFERENCIA,
)

TIPOS = ["EXTENDS", "IMPLEMENTS", "ASSOCIATES", "COMPOSED_OF", "AGGREGATES", "DEPENDS_ON"]
TIPOS_COM_PAPEL = ("ASSOCIATES", "COMPOSED_OF", "AGGREGATES")
MULTIPLICIDADES = ["1", "0..1", "*", "1..*", "0..*", "2..5", "3"]
PAPEIS = ["items", "owner", "payment", "customer", "lines"]
PACOTES = ["domain", "service", "repository", "infra"]
KINDS = ["class", "interface", "enum"]
VISIBILIDADES = ["public", "private", "protected"]

MUTACOES = ["remover_id", "duplicar_id", "referencia_inexistente", "multiplicidade_vazia", "linhas_201"]
REGRA_ESPERADA = {
    "remover_id": R_ID_VAZIO,
    "duplicar_id": R_ID_DUPLICADO,
    "referencia_inexistente": R_REFERENCIA,
    "multiplicidade_vazia": R_MULTIPLICIDADE,
    "linhas_201": R_MAX_LINHAS,
}


def _rel(source: str, target: str, tipo: str, role: str, mult: str) -> dict:
    if tipo in TIPOS_COM_PAPEL:
        return dict(sourceId=source, targetId=target, type=tipo, role=role, multiplicity=mult)
    return dict(sourceId=source, targetId=target, type=tipo, role="", multiplicity="")


@st.composite
def valid_datasets(draw) -> Dataset:
    """Dataset válido: 2-12 classificadores, até 30 relacionamentos, com ciclo e cadeia EXTENDS."""
    n = draw(st.integers(2, 12))
    ids = [f"c{i}" for i in range(n)]
    ds = Dataset.empty()
    for cid in ids:
        ds.classifiers.add(
            id=cid, name=f"Name{cid}", kind=draw(st.sampled_from(KINDS)),
            isAbstract=draw(st.sampled_from(["true", "false"])),
            package=draw(st.sampled_from(PACOTES)),
        )

    ident = st.sampled_from(ids)
    papel = st.sampled_from(PAPEIS)
    mult = st.sampled_from(MULTIPLICIDADES)

    rels = [_rel(ids[0], ids[1], "ASSOCIATES", draw(papel), draw(mult))]
    # cadeia EXTENDS c0 -> c1 -> ... -> c(k)
    k = draw(st.integers(2, n))
    rels += [_rel(ids[i], ids[i + 1], "EXTENDS", "", "") for i in range(k - 1)]
    # ciclo entre classificadores distintos
    ciclo = draw(st.lists(ident, min_size=2, max_size=5, unique=True))
    for a, b in zip(ciclo, ciclo[1:] + ciclo[:1]):
        rels.append(_rel(a, b, draw(st.sampled_from(TIPOS)), draw(papel), draw(mult)))
    # arestas aleatórias (inclui auto-relacionamento e paralelas)
    extras = draw(st.lists(st.tuples(ident, ident, st.sampled_from(TIPOS), papel, mult), max_size=30))
    rels += [_rel(*e) for e in extras]
    for r in rels[:30]:
        ds.relationships.add(**r)

    n_met = draw(st.integers(2, 6))
    mids = [f"m{i}" for i in range(n_met)]
    for i, mid in enumerate(mids):
        ds.methods.add(
            id=mid, classifierId=draw(ident), name=f"met{i}", returnType="void",
            visibility=draw(st.sampled_from(VISIBILIDADES)), isStatic="false",
            isAbstract="false", position=str(i),
        )
    for i in range(draw(st.integers(1, 6))):
        ds.attributes.add(
            id=f"a{i}", classifierId=draw(ident), name=f"att{i}", dataType="String",
            visibility=draw(st.sampled_from(VISIBILIDADES)), isStatic="false", position=str(i),
        )
    for i in range(draw(st.integers(1, 6))):
        ds.calls.add(callerId=draw(st.sampled_from(mids)), calleeId=draw(st.sampled_from(mids)),
                     sequence=str(i))
    return ds


def _mutate(ds: Dataset, mutacao: str, indice: int) -> Dataset:
    ds = copy.deepcopy(ds)
    if mutacao == "remover_id":
        ds.classifiers.rows[indice % len(ds.classifiers.rows)]["id"] = ""
    elif mutacao == "duplicar_id":
        rows = ds.classifiers.rows
        j = indice % (len(rows) - 1) + 1  # nunca a linha 0
        rows[j]["id"] = rows[0]["id"]
    elif mutacao == "referencia_inexistente":
        row = ds.relationships.rows[indice % len(ds.relationships.rows)]
        row["targetId" if indice % 2 else "sourceId"] = "inexistente"
    elif mutacao == "multiplicidade_vazia":
        com_papel = [r for r in ds.relationships.rows if r["type"] in TIPOS_COM_PAPEL]
        com_papel[indice % len(com_papel)]["multiplicity"] = ""
    elif mutacao == "linhas_201":
        base = ds.relationships.rows[0]
        while len(ds.relationships.rows) < 201:
            ds.relationships.rows.append(dict(base))
    return ds


@st.composite
def invalid_datasets(draw) -> tuple[Dataset, str, str]:
    """Devolve (dataset inválido, nome da mutação, regra que deve ser reportada)."""
    ds = draw(valid_datasets())
    mutacao = draw(st.sampled_from(MUTACOES))
    indice = draw(st.integers(0, 1000))
    return _mutate(ds, mutacao, indice), mutacao, REGRA_ESPERADA[mutacao]
