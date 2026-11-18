"""Testes de exemplo do dataset real em data/.

Validates: Requirements 5.1, 5.2, 5.5, 5.6, 5.7
"""

from __future__ import annotations

from itertools import permutations

import pytest

from tests.helpers.dataset_model import TABLE_NAMES, read_dataset
from tests.helpers.validator import validate

TIPOS_UML = {
    "EXTENDS", "IMPLEMENTS", "ASSOCIATES", "COMPOSED_OF", "AGGREGATES", "DEPENDS_ON",
}
CAMADAS_PROIBIDAS = {"service", "repository", "infra"}


@pytest.fixture(scope="module")
def dataset(data_dir):
    return read_dataset(data_dir)


def test_cinco_arquivos_presentes_e_utf8(data_dir):
    for nome in TABLE_NAMES:
        caminho = data_dir / f"{nome}.csv"
        assert caminho.is_file(), f"arquivo ausente: {caminho}"
        caminho.read_bytes().decode("utf-8")  # levanta se nao for UTF-8


def test_validador_sem_erros(dataset):
    assert validate(dataset) == []


def test_exatamente_16_classificadores(dataset):
    assert len(dataset.classifiers.rows) == 16


def test_todos_os_seis_tipos_de_relacionamento_presentes(dataset):
    tipos = {r["type"] for r in dataset.relationships.rows}
    assert TIPOS_UML <= tipos


def _arestas_depends_on(dataset) -> dict[str, set[str]]:
    grafo: dict[str, set[str]] = {}
    for r in dataset.relationships.rows:
        grafo.setdefault(r["sourceId"], set()).add(r["targetId"])
    return grafo


def test_existe_ciclo_de_2_a_5_classificadores_distintos(dataset):
    grafo = _arestas_depends_on(dataset)
    ids = sorted({c["id"] for c in dataset.classifiers.rows})
    encontrado = False
    for tamanho in range(2, 6):
        for seq in permutations(ids, tamanho):
            if all(seq[(i + 1) % tamanho] in grafo.get(seq[i], ()) for i in range(tamanho)):
                encontrado = True
                break
        if encontrado:
            break
    assert encontrado


def test_payment_stripe_e_a_unica_dependencia_de_domain_para_camadas_inferiores(dataset):
    pacote = {c["id"]: c["package"] for c in dataset.classifiers.rows}
    violacoes = [
        (r["sourceId"], r["targetId"])
        for r in dataset.relationships.rows
        if pacote[r["sourceId"]] == "domain" and pacote[r["targetId"]] in CAMADAS_PROIBIDAS
    ]
    assert violacoes == [("Payment", "StripeGateway")]
    tipos = [
        r["type"]
        for r in dataset.relationships.rows
        if (r["sourceId"], r["targetId"]) == ("Payment", "StripeGateway")
    ]
    assert tipos == ["DEPENDS_ON"]
