"""Configuracao compartilhada da suite de testes."""

from pathlib import Path

import pytest
from hypothesis import settings

from helpers.neo4j_fixture import neo4j_db  # noqa: F401  (registra a fixture de sessão)

settings.register_profile("portfolio", max_examples=100, deadline=None)
settings.load_profile("portfolio")

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Raiz do repositorio."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def data_dir(repo_root: Path) -> Path:
    """Pasta data/ com os CSVs do dataset."""
    return repo_root / "data"


@pytest.fixture(scope="session")
def cypher_dir(repo_root: Path) -> Path:
    """Pasta cypher/ com os scripts."""
    return repo_root / "cypher"
