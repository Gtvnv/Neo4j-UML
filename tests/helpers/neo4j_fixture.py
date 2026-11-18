"""Fixture de Neo4j 5.x Community (sem APOC) via testcontainers.

O módulo pode ser importado sem Docker, sem testcontainers e sem o driver `neo4j`:
essas dependências são importadas apenas ao subir o contêiner. Sem Docker, os testes
que usam a fixture `neo4j_db` são ignorados com mensagem explícita.

Uso em um teste:

    pytestmark = pytest.mark.neo4j

    def test_algo(neo4j_db):
        neo4j_db.reset()
        neo4j_db.write_dataset(ds)
        neo4j_db.run_script("01_constraints.cypher")
        neo4j_db.run_script("02_load.cypher")
"""

from __future__ import annotations

import os
import re
import secrets
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

import pytest

from .dataset_model import Dataset, write_dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
CYPHER_DIR = REPO_ROOT / "cypher"
DATA_DIR = REPO_ROOT / "data"

DEFAULT_IMAGE = "neo4j:5.26-community"
IMPORT_DIR_IN_CONTAINER = "/var/lib/neo4j/import"
BOLT_PORT = 7687


# --------------------------------------------------------------------------- divisor

def split_statements(text: str) -> list[str]:
    """Divide um script Cypher em instruções separadas por `;` fora de comentários e literais.

    - comentários `// ...` e `/* ... */` são removidos do texto das instruções;
    - literais com aspas simples, aspas duplas e crases preservam o `;` e comentários internos
      (aspas simples e duplas aceitam escape com barra invertida);
    - instruções vazias (só espaços ou comentários) são descartadas;
    - o `;` final não faz parte da instrução devolvida.
    """
    statements: list[str] = []
    buf: list[str] = []
    i, n = 0, len(text)

    def flush() -> None:
        stmt = "".join(buf).strip()
        if stmt:
            statements.append(stmt)
        buf.clear()

    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            buf.append(" ")
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
            i += 1
            while i < n:
                c = text[i]
                buf.append(c)
                i += 1
                if c == "\\" and quote != "`" and i < n:
                    buf.append(text[i])
                    i += 1
                elif c == quote:
                    break
            continue
        if ch == ";":
            flush()
            i += 1
            continue
        buf.append(ch)
        i += 1
    flush()
    return statements


# --------------------------------------------------------------------------- consultas Qnn

QUERIES_FILE = "03_queries.cypher"
_QUERY_HEADER = re.compile(r"^\s*//\s*(Q\d{2})\s*-")
_PARAM_LINE = re.compile(r"^\s*:param\s+(\w+)\s*(?:=>|=)\s*(.+?)\s*;?\s*$")


def extract_queries(text: str) -> dict[str, str]:
    """Extrai o texto de cada `Qnn` de um script de consultas.

    A consulta começa na linha seguinte ao comentário `// Qnn - ...` e termina no `;`
    (que não faz parte do texto). Linhas `:param` e comentários internos são ignorados.
    """
    queries: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        header = _QUERY_HEADER.match(line)
        if header and current is None:
            current, buf = header.group(1), []
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith(":param"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            body = "\n".join(buf).strip()
            queries[current] = body[:-1].rstrip()
            current = None
    return queries


def parse_param_defaults(text: str) -> dict[str, Any]:
    """Lê as linhas `:param nome => 'valor'` e devolve os valores (texto ou número)."""
    params: dict[str, Any] = {}
    for line in text.splitlines():
        m = _PARAM_LINE.match(line)
        if not m:
            continue
        raw = m.group(2)
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
            params[m.group(1)] = raw[1:-1]
        else:
            try:
                params[m.group(1)] = int(raw)
            except ValueError:
                params[m.group(1)] = raw
    return params


def load_queries(path: Path | None = None) -> dict[str, str]:
    """Consultas Qnn de `cypher/03_queries.cypher` (ou de `path`)."""
    return extract_queries((path or CYPHER_DIR / QUERIES_FILE).read_text(encoding="utf-8"))


def run_query(db: "Neo4jDb", qid: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Executa a consulta `qid` (ex.: "Q03") com os parâmetros dados.

    Sem o parâmetro exigido, o driver falha com erro de parâmetro ausente.
    """
    queries = load_queries()
    if qid not in queries:
        raise KeyError(f"Consulta {qid} não encontrada em {QUERIES_FILE}")
    return db.run(queries[qid], **(params or {}))


# --------------------------------------------------------------------------- fixture

class Neo4jDb:
    """Contêiner Neo4j descartável com pasta `import` montada do host."""

    def __init__(self, image: str | None = None) -> None:
        self.image = image or os.environ.get("NEO4J_TEST_IMAGE", DEFAULT_IMAGE)
        self.import_dir = Path(tempfile.mkdtemp(prefix="neo4j-import-"))
        self._container: Any = None
        self._driver: Any = None

    # -- ciclo de vida
    def start(self) -> None:
        from neo4j import GraphDatabase
        from testcontainers.core.container import DockerContainer
        from testcontainers.core.waiting_utils import wait_for_logs

        # permite que o usuário do contêiner leia os CSVs montados
        os.chmod(self.import_dir, 0o777)
        password = secrets.token_urlsafe(12)
        container = (
            DockerContainer(self.image)
            .with_env("NEO4J_AUTH", f"neo4j/{password}")
            .with_exposed_ports(BOLT_PORT)
            .with_volume_mapping(str(self.import_dir), IMPORT_DIR_IN_CONTAINER, "rw")
        )
        container.start()
        self._container = container
        wait_for_logs(container, "Started.", timeout=180)
        url = f"bolt://{container.get_container_host_ip()}:{container.get_exposed_port(BOLT_PORT)}"
        self._driver = GraphDatabase.driver(url, auth=("neo4j", password))
        self._driver.verify_connectivity()

    def stop(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
        if self._container is not None:
            self._container.stop()
            self._container = None
        shutil.rmtree(self.import_dir, ignore_errors=True)

    # -- arquivos
    def write_dataset(self, ds: Dataset) -> None:
        """Grava os cinco CSVs na pasta `import` do contêiner."""
        write_dataset(ds, self.import_dir)
        for f in self.import_dir.glob("*.csv"):
            f.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    def copy_real_dataset(self) -> None:
        """Copia os CSVs reais de `data/` para a pasta `import`."""
        for f in DATA_DIR.glob("*.csv"):
            shutil.copyfile(f, self.import_dir / f.name)
            (self.import_dir / f.name).chmod(0o644)

    # -- execução
    def run(self, cypher: str, **params: Any) -> list[dict[str, Any]]:
        """Executa uma instrução em transação própria (auto-commit) e devolve as linhas."""
        with self._driver.session() as session:
            return [dict(r) for r in session.run(cypher, **params)]

    def run_statements(self, statements: list[str]) -> list[list[dict[str, Any]]]:
        """Executa cada instrução em sua própria transação, parando no primeiro erro."""
        return [self.run(s) for s in statements]

    def run_script(
        self, script: str | Path, *, limit: int | None = None
    ) -> list[list[dict[str, Any]]]:
        """Executa um script de `cypher/` (nome ou caminho).

        `limit` executa só as primeiras N instruções, para simular carga interrompida.
        """
        path = Path(script)
        if not path.is_absolute():
            path = CYPHER_DIR / path
        statements = split_statements(path.read_text(encoding="utf-8"))
        if limit is not None:
            statements = statements[:limit]
        return self.run_statements(statements)

    def run_query(self, qid: str, **params: Any) -> list[dict[str, Any]]:
        """Executa a consulta Qnn de `03_queries.cypher` com os parâmetros dados."""
        return run_query(self, qid, params)

    def reset(self) -> None:
        """Executa o 99_reset.cypher: remove nós do projeto e as quatro constraints."""
        self.run_script("99_reset.cypher")

    def clear_import(self) -> None:
        for f in self.import_dir.glob("*.csv"):
            f.unlink()


def docker_unavailable_reason() -> str | None:
    """Devolve o motivo da indisponibilidade do Docker ou None se estiver acessível."""
    try:
        import docker  # dependência do testcontainers
    except ImportError as exc:
        return f"pacote 'docker'/'testcontainers' não instalado ({exc})"
    try:
        docker.from_env().ping()
    except Exception as exc:  # noqa: BLE001 - qualquer falha significa Docker indisponível
        return f"daemon do Docker inacessível ({type(exc).__name__}: {exc})"
    try:
        import neo4j  # noqa: F401
    except ImportError as exc:
        return f"driver 'neo4j' não instalado ({exc})"
    return None


@pytest.fixture(scope="session")
def neo4j_db():
    """Neo4j 5.x Community sem APOC, um contêiner por sessão de testes."""
    reason = docker_unavailable_reason()
    if reason:
        pytest.skip(f"Testes com Neo4j ignorados: Docker indisponível. {reason}")
    db = Neo4jDb()
    try:
        db.start()
    except Exception as exc:  # noqa: BLE001
        db.stop()
        pytest.skip(f"Testes com Neo4j ignorados: não foi possível subir o contêiner. {exc}")
    try:
        yield db
    finally:
        db.stop()
