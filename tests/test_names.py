"""Feature: neo4j-uml-graph-portfolio, Property 13: Nomes e identificadores seguem os padrões exigidos.

**Validates: Requirements 1.2, 8.7, 11.1, 11.2**
"""

import re
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

SCRIPT_RE = re.compile(r"\d{2}_[a-z0-9_]+\.cypher", re.ASCII)
EVIDENCE_RE = re.compile(r"q\d{2}-[a-z0-9-]{1,60}\.png", re.ASCII)
PASCAL_RE = re.compile(r"[A-Z][a-zA-Z0-9]*", re.ASCII)
UPPER_SNAKE_RE = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*", re.ASCII)
CAMEL_RE = re.compile(r"[a-z][a-zA-Z0-9]*", re.ASCII)


def is_script_name(text: str) -> bool:
    """NN_descricao.cypher com NN entre 01 e 99."""
    return SCRIPT_RE.fullmatch(text) is not None and text[:2] != "00"


def is_evidence_name(text: str) -> bool:
    """qNN-descricao-kebab.png, descricao de 1 a 60 caracteres, sem acento."""
    return EVIDENCE_RE.fullmatch(text) is not None


def is_pascal_case(text: str) -> bool:
    return PASCAL_RE.fullmatch(text) is not None


def is_upper_snake_case(text: str) -> bool:
    return UPPER_SNAKE_RE.fullmatch(text) is not None


def is_camel_case(text: str) -> bool:
    return CAMEL_RE.fullmatch(text) is not None


# Estrategias que misturam texto arbitrario com candidatos proximos do padrao.
_alphabet = st.sampled_from(list("abcxyz019_-.AZé ç\nq"))
_noise = st.text(_alphabet, max_size=30)


def _script_candidates():
    return st.one_of(
        st.text(max_size=20),
        _noise,
        st.builds(
            lambda n, d: f"{n:02d}_{d}.cypher",
            st.integers(0, 99),
            st.text("abcxyz019_-AZé", max_size=15),
        ),
    )


def _evidence_candidates():
    return st.one_of(
        st.text(max_size=20),
        _noise,
        st.builds(
            lambda n, d: f"q{n:02d}-{d}.png",
            st.integers(0, 99),
            st.text("abcxyz019-_Aé", max_size=70),
        ),
    )


@given(_script_candidates())
def test_script_name_accepts_iff_pattern(text):
    expected = (
        re.fullmatch(r"[0-9]{2}_[a-z0-9_]+\.cypher", text) is not None
        and 1 <= int(text[:2]) <= 99
    )
    assert is_script_name(text) == expected


@given(_evidence_candidates())
def test_evidence_name_accepts_iff_pattern(text):
    m = re.fullmatch(r"q[0-9]{2}-([a-z0-9-]+)\.png", text)
    expected = m is not None and 1 <= len(m.group(1)) <= 60
    assert is_evidence_name(text) == expected


@pytest.mark.parametrize("name", ["01_constraints.cypher", "99_reset.cypher", "10_a.cypher"])
def test_script_name_examples_valid(name):
    assert is_script_name(name)


@pytest.mark.parametrize(
    "name",
    ["00_x.cypher", "1_x.cypher", "01-x.cypher", "01_X.cypher", "01_x.cypher\n", "01_x.txt", "01_é.cypher"],
)
def test_script_name_examples_invalid(name):
    assert not is_script_name(name)


@pytest.mark.parametrize("name", ["q01-acoplamento.png", "q10-a-b-c.png", "q01-" + "a" * 60 + ".png"])
def test_evidence_name_examples_valid(name):
    assert is_evidence_name(name)


@pytest.mark.parametrize(
    "name",
    ["q1-x.png", "q01-.png", "q01-" + "a" * 61 + ".png", "q01-Ação.png", "q01-ação.png", "q01-x_y.png", "Q01-x.png", "q01-x.png\n"],
)
def test_evidence_name_examples_invalid(name):
    assert not is_evidence_name(name)


@pytest.mark.parametrize(
    "validator,valid,invalid",
    [
        (is_pascal_case, ["Classifier", "StripeGateway", "A1"], ["classifier", "Stripe_Gateway", "", "1A", "Ação"]),
        (is_upper_snake_case, ["DEPENDS_ON", "REALIZES", "A1_B2"], ["depends_on", "Depends_On", "_A", "A_", "A__B", ""]),
        (is_camel_case, ["name", "sequenceNumber", "id"], ["Name", "sequence_number", "", "1a", "açao"]),
    ],
)
def test_case_validators_examples(validator, valid, invalid):
    assert all(validator(v) for v in valid)
    assert not any(validator(v) for v in invalid)


@given(st.text(max_size=30))
def test_case_validators_match_reference_regex(text):
    assert is_pascal_case(text) == bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", text, re.ASCII))
    assert is_camel_case(text) == bool(re.fullmatch(r"[a-z][A-Za-z0-9]*", text, re.ASCII))
    assert is_upper_snake_case(text) == bool(
        re.fullmatch(r"[A-Z][A-Z0-9]*(_[A-Z0-9]+)*", text, re.ASCII)
    )


def test_cypher_folder_names_valid_and_prefixes_unique(cypher_dir: Path):
    files = sorted(p.name for p in cypher_dir.glob("*.cypher"))
    assert files, "cypher/ sem scripts"
    bad = [f for f in files if not is_script_name(f)]
    assert not bad, f"nomes fora do padrão: {bad}"
    prefixes = [f[:2] for f in files]
    assert len(prefixes) == len(set(prefixes)), f"prefixos repetidos: {prefixes}"


@pytest.mark.evidencias
def test_one_evidence_per_question(repo_root: Path):
    """Um arquivo qNN-*.png por pergunta do 03_queries.cypher (roda na tarefa 10.2)."""
    queries = (repo_root / "cypher" / "03_queries.cypher").read_text(encoding="utf-8")
    numbers = sorted(set(re.findall(r"\bQ(\d{2})\b", queries)))
    assert numbers, "nenhuma pergunta Qnn encontrada"
    images = sorted(p.name for p in (repo_root / "docs" / "images").glob("q*.png"))
    assert all(is_evidence_name(n) for n in images), images
    for nn in numbers:
        matches = [n for n in images if n.startswith(f"q{nn}-")]
        assert len(matches) == 1, f"Q{nn}: esperado 1 arquivo, achei {matches}"
