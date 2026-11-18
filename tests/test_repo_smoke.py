"""Testes de exemplo do repositório e do README (puros, sem banco).

Validates: Requirements 1.1, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.4, 3.5,
4.1, 9.10, 12.5, 12.6
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.helpers.dataset_model import read_dataset
from tests.helpers.oracles import expected_node_counts, expected_relationship_counts

GITIGNORE_OBRIGATORIO = [
    ".DS_Store", "Thumbs.db", ".idea/", ".vscode/", ".vs/",
    "neo4j/data/", "neo4j/logs/", "neo4j/import/",
]
PASTAS_OBRIGATORIAS = ["data", "cypher", "docs/images"]
SCRIPTS_EM_ORDEM = ["01_constraints", "02_load", "04_validate", "03_queries"]
PLACEHOLDER = "<sua-senha>"


@pytest.fixture(scope="module")
def readme(repo_root: Path) -> str:
    return (repo_root / "README.md").read_text(encoding="utf-8")


def secao(texto: str, titulo: str, nivel: int = 2) -> str:
    """Corpo da seção cujo título começa com `titulo`, até o próximo título de mesmo nível ou superior."""
    marca = "#" * nivel
    linhas = texto.splitlines()
    corpo: list[str] = []
    dentro = False
    em_codigo = False
    for linha in linhas:
        if linha.startswith("```"):
            em_codigo = not em_codigo
        titulo_atual = None if em_codigo else re.match(r"^(#+)\s+(.*)$", linha)
        if titulo_atual and not em_codigo:
            if dentro and len(titulo_atual.group(1)) <= nivel:
                break
            if not dentro and len(titulo_atual.group(1)) == nivel and titulo_atual.group(2).startswith(titulo):
                dentro = True
                continue
        if dentro:
            corpo.append(linha)
    assert dentro, f"secao ausente: {marca} {titulo}"
    return "\n".join(corpo)


def blocos_codigo(texto: str) -> list[tuple[str, str]]:
    return [(m.group(1).strip().lower(), m.group(2)) for m in re.finditer(r"```([^\n]*)\n(.*?)```", texto, re.S)]


# ---------------------------------------------------------------- repositório

def test_readme_presente(repo_root):
    assert (repo_root / "README.md").is_file()


def test_license_com_ano_e_titular(repo_root):
    texto = (repo_root / "LICENSE").read_text(encoding="utf-8")
    assert texto.strip()
    m = re.search(r"^Copyright \(c\) ((?:19|20)\d{2})\s+(\S.*)$", texto, re.M)
    assert m, "LICENSE sem linha 'Copyright (c) <ano> <titular>'"


def test_gitignore_entradas_obrigatorias(repo_root):
    linhas = {l.strip() for l in (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()}
    faltando = [e for e in GITIGNORE_OBRIGATORIO if e not in linhas]
    assert not faltando, f"entradas ausentes no .gitignore: {faltando}"


@pytest.mark.parametrize("pasta", PASTAS_OBRIGATORIAS)
def test_pastas_obrigatorias(repo_root, pasta):
    assert (repo_root / pasta).is_dir()


# ---------------------------------------------------------------- README: seções

def test_contexto_100_a_300_palavras(readme):
    palavras = re.findall(r"\w+", secao(readme, "Contexto"), re.UNICODE)
    assert 100 <= len(palavras) <= 300, f"{len(palavras)} palavras"


def test_justificativa_com_cypher_e_sql(readme):
    corpo = secao(readme, "Justificativa")
    linguagens = {lang for lang, codigo in blocos_codigo(corpo) if codigo.strip()}
    assert "cypher" in linguagens
    assert "sql" in linguagens


def test_todos_os_pacotes_citados(readme, data_dir):
    ds = read_dataset(data_dir)
    pacotes = {r["package"] for r in ds.classifiers.rows if r["package"]}
    assert pacotes
    faltando = [p for p in sorted(pacotes) if not re.search(rf"`{re.escape(p)}`", readme)]
    assert not faltando, f"pacotes nao citados: {faltando}"


def test_passos_desktop_e_docker(readme):
    desktop = secao(readme, "Execução no Neo4j Desktop", nivel=3)
    assert len(re.findall(r"^\d+\.\s", desktop, re.M)) >= 2
    docker = secao(readme, "Execução com Docker", nivel=3)
    assert any("docker run" in codigo for _, codigo in blocos_codigo(docker))


def test_ordem_dos_scripts(readme):
    corpo = secao(readme, "Ordem de execução dos scripts", nivel=3)
    itens = re.findall(r"^\d+\.\s+`cypher/(\d{2}_[a-z]+)\.cypher`", corpo, re.M)
    assert itens == SCRIPTS_EM_ORDEM


def test_troubleshooting_5_a_15_itens_com_rotulos(readme):
    corpo = secao(readme, "Troubleshooting")
    partes = re.split(r"^### ", corpo, flags=re.M)[1:]
    assert 5 <= len(partes) <= 15, f"{len(partes)} itens"
    for parte in partes:
        for rotulo in ("Sintoma", "Causa", "Solução"):
            assert f"**{rotulo}:**" in parte, f"rotulo {rotulo} ausente em: {parte.splitlines()[0]}"


def test_tabela_de_perguntas_uma_linha_por_pergunta(readme):
    corpo = secao(readme, "Perguntas de negócio")
    ids = re.findall(r"^\|\s*Q(0[1-8])\.", corpo, re.M)
    assert sorted(ids) == [f"0{i}" for i in range(1, 9)]


# ---------------------------------------------------------------- README: contagens

def _tabela_contagens(corpo: str, cabecalho: str) -> dict[str, int]:
    resultado: dict[str, int] = {}
    ativo = False
    for linha in corpo.splitlines():
        if linha.startswith("|") and cabecalho in linha:
            ativo = True
            continue
        if ativo:
            if not linha.startswith("|"):
                break
            m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|", linha)
            if m:
                resultado[m.group(1)] = int(m.group(2))
    assert resultado, f"tabela '{cabecalho}' nao encontrada"
    return resultado


def test_contagens_do_readme_iguais_ao_oraculo(readme, data_dir):
    ds = read_dataset(data_dir)
    corpo = secao(readme, "Contagens esperadas", nivel=3)
    assert _tabela_contagens(corpo, "Label") == expected_node_counts(ds)
    assert _tabela_contagens(corpo, "Tipo de relacionamento") == expected_relationship_counts(ds)


# ---------------------------------------------------------------- segredos

def _padroes_segredo() -> list[re.Pattern[str]]:
    # Montados por fragmentos para o proprio arquivo nao casar com a varredura.
    return [
        re.compile("AK" + r"IA[0-9A-Z]{16}"),
        re.compile("gh" + r"[pousr]_[A-Za-z0-9]{30,}"),
        re.compile("sk" + r"-[A-Za-z0-9]{20,}"),
        re.compile("-----BEGIN [A-Z ]*PRIV" + "ATE KEY-----"),
        re.compile("xo" + r"x[abp]-[A-Za-z0-9-]{10,}"),
        re.compile(r"(?i)\b(?:pass" + r"word|passw" + r"d|secr" + r"et|tok" + r"en)\b\s*[=:]\s*['\"]?(?!<)[^\s'\"<]{4,}"),
    ]


def _arquivos_texto(repo_root: Path):
    ignoradas = {".git", ".kiro", ".hypothesis", ".pytest_cache", "__pycache__", ".venv", "tests"}
    for caminho in repo_root.rglob("*"):
        rel = caminho.relative_to(repo_root)
        if not caminho.is_file() or ignoradas & set(rel.parts):
            continue
        if caminho.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ini"}:
            continue
        yield caminho


def test_sem_padroes_de_segredo(repo_root):
    achados = []
    for caminho in _arquivos_texto(repo_root):
        try:
            texto = caminho.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for padrao in _padroes_segredo():
            if padrao.search(texto):
                achados.append(f"{caminho.relative_to(repo_root)}: {padrao.pattern[:20]}")
    assert not achados, achados


def test_comandos_com_credencial_usam_placeholder(readme):
    for _, codigo in blocos_codigo(readme):
        for linha in codigo.splitlines():
            if re.search(r"NEO4J_AUTH|--password|-p\s+\S+\s+.*cypher-shell|cypher-shell.*\s-p\s", linha):
                assert PLACEHOLDER in linha, f"credencial sem placeholder: {linha}"
    assert PLACEHOLDER in readme
