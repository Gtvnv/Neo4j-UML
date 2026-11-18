"""Validador do dataset: implementa as regras do Requirement 5.

Numeração de linhas: a linha 1 é o cabeçalho e a primeira linha de dados é a 2.
Erros que dizem respeito ao arquivo todo (cabeçalho, quantidade de linhas) usam a linha 1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .dataset_model import (
    ATTRIBUTES,
    CALLS,
    CLASSIFIERS,
    EXPECTED_HEADERS,
    METHODS,
    RELATIONSHIPS,
    TABLE_NAMES,
    Dataset,
)

MAX_LINHAS = 200
MULTIPLICITY_RE = re.compile(r"^(\d+|\*)(\.\.(\d+|\*))?$")
TIPOS_COM_PAPEL = ("ASSOCIATES", "COMPOSED_OF", "AGGREGATES")

# Nomes das regras
R_CABECALHO = "cabecalho"
R_MIN_LINHAS = "minimo-1-linha"
R_MAX_LINHAS = "maximo-200-linhas"
R_ID_VAZIO = "id-vazio"
R_ID_DUPLICADO = "id-duplicado"
R_REFERENCIA = "referencia-nao-resolvida"
R_ROLE = "role-vazio"
R_MULTIPLICIDADE = "multiplicidade-invalida"


@dataclass(frozen=True)
class Erro:
    arquivo: str
    regra: str
    linha: int
    mensagem: str


def validate(dataset: Dataset) -> list[Erro]:
    erros: list[Erro] = []
    ok: set[str] = set()  # tabelas com cabeçalho correto (linhas só são checadas nelas)

    for name in TABLE_NAMES:
        table = dataset.table(name)
        arquivo = f"{name}.csv"
        if table.header != EXPECTED_HEADERS[name]:
            erros.append(Erro(arquivo, R_CABECALHO, 1,
                              f"cabeçalho esperado {EXPECTED_HEADERS[name]}, obtido {table.header}"))
        else:
            ok.add(name)
        if len(table.rows) < 1:
            erros.append(Erro(arquivo, R_MIN_LINHAS, 1, "o arquivo precisa de ao menos 1 linha de dados"))
        if len(table.rows) > MAX_LINHAS:
            erros.append(Erro(arquivo, R_MAX_LINHAS, MAX_LINHAS + 2,
                              f"{len(table.rows)} linhas de dados, máximo {MAX_LINHAS}"))

    classifier_ids = _check_classifier_ids(dataset, ok, erros)
    method_ids = _ids(dataset, METHODS, ok)

    if RELATIONSHIPS in ok:
        _check_relationships(dataset, classifier_ids, erros)
    for name in (ATTRIBUTES, METHODS):
        if name in ok:
            _check_refs(dataset, name, "classifierId", classifier_ids, erros)
    if CALLS in ok:
        _check_refs(dataset, CALLS, "callerId", method_ids, erros)
        _check_refs(dataset, CALLS, "calleeId", method_ids, erros)
    return erros


def _ids(dataset: Dataset, name: str, ok: set[str]) -> set[str]:
    if name not in ok:
        return set()
    return {r["id"] for r in dataset.table(name).rows if r["id"] != ""}


def _check_classifier_ids(dataset: Dataset, ok: set[str], erros: list[Erro]) -> set[str]:
    if CLASSIFIERS not in ok:
        return set()
    vistos: set[str] = set()
    for i, row in enumerate(dataset.classifiers.rows):
        linha = i + 2
        valor = row["id"]
        if valor.strip() == "":
            erros.append(Erro("classifiers.csv", R_ID_VAZIO, linha, "id do classificador vazio"))
        elif valor in vistos:
            erros.append(Erro("classifiers.csv", R_ID_DUPLICADO, linha, f"id duplicado: {valor!r}"))
        else:
            vistos.add(valor)
    return vistos


def _check_refs(dataset: Dataset, name: str, coluna: str, validos: set[str], erros: list[Erro]) -> None:
    for i, row in enumerate(dataset.table(name).rows):
        if row[coluna] not in validos:
            erros.append(Erro(f"{name}.csv", R_REFERENCIA, i + 2,
                              f"{coluna}={row[coluna]!r} não existe"))


def _check_relationships(dataset: Dataset, classifier_ids: set[str], erros: list[Erro]) -> None:
    _check_refs(dataset, RELATIONSHIPS, "sourceId", classifier_ids, erros)
    _check_refs(dataset, RELATIONSHIPS, "targetId", classifier_ids, erros)
    for i, row in enumerate(dataset.relationships.rows):
        if row["type"] not in TIPOS_COM_PAPEL:
            continue
        linha = i + 2
        if row["role"].strip() == "":
            erros.append(Erro("relationships.csv", R_ROLE, linha, f"role vazio em {row['type']}"))
        if not MULTIPLICITY_RE.fullmatch(row["multiplicity"]):
            erros.append(Erro("relationships.csv", R_MULTIPLICIDADE, linha,
                              f"multiplicity {row['multiplicity']!r} fora da notação UML"))
