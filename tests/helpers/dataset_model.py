"""Modelo em memória do dataset (cinco tabelas) com leitura e escrita de CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

CLASSIFIERS = "classifiers"
RELATIONSHIPS = "relationships"
ATTRIBUTES = "attributes"
METHODS = "methods"
CALLS = "calls"

TABLE_NAMES = (CLASSIFIERS, RELATIONSHIPS, ATTRIBUTES, METHODS, CALLS)

EXPECTED_HEADERS: dict[str, list[str]] = {
    CLASSIFIERS: ["id", "name", "kind", "isAbstract", "package"],
    RELATIONSHIPS: ["sourceId", "targetId", "type", "role", "multiplicity"],
    ATTRIBUTES: [
        "id", "classifierId", "name", "dataType", "visibility", "isStatic", "position",
    ],
    METHODS: [
        "id", "classifierId", "name", "returnType", "visibility",
        "isStatic", "isAbstract", "position",
    ],
    CALLS: ["callerId", "calleeId", "sequence"],
}


@dataclass
class Table:
    """Uma tabela CSV: cabeçalho lido do arquivo e linhas de dados como dicionários."""

    header: list[str]
    rows: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def empty(cls, name: str) -> "Table":
        return cls(header=list(EXPECTED_HEADERS[name]), rows=[])

    def add(self, **values: str) -> None:
        self.rows.append({col: str(values.get(col, "")) for col in self.header})


@dataclass
class Dataset:
    classifiers: Table
    relationships: Table
    attributes: Table
    methods: Table
    calls: Table

    @classmethod
    def empty(cls) -> "Dataset":
        return cls(*(Table.empty(n) for n in TABLE_NAMES))

    def table(self, name: str) -> Table:
        return getattr(self, name)


def read_table(path: Path) -> Table:
    """Lê um CSV UTF-8 com cabeçalho. Arquivo vazio gera cabeçalho vazio e nenhuma linha."""
    with open(path, newline="", encoding="utf-8") as fh:
        records = [r for r in csv.reader(fh) if r]
    if not records:
        return Table(header=[], rows=[])
    header, data = records[0], records[1:]
    rows = [
        {col: (rec[i] if i < len(rec) else "") for i, col in enumerate(header)}
        for rec in data
    ]
    return Table(header=header, rows=rows)


def write_table(table: Table, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(table.header)
        for row in table.rows:
            writer.writerow([row.get(col, "") for col in table.header])


def read_dataset(directory: Path) -> Dataset:
    return Dataset(*(read_table(Path(directory) / f"{n}.csv") for n in TABLE_NAMES))


def write_dataset(dataset: Dataset, directory: Path) -> None:
    for name in TABLE_NAMES:
        write_table(dataset.table(name), Path(directory) / f"{name}.csv")
