"""Property 14: scripts Cypher nao usam APOC nem CREATE de dados.

**Validates: Requirements 7.2, 7.5, 12.3, 12.4**
"""

import re

from hypothesis import given, strategies as st

APOC_RE = re.compile(r"apoc\.", re.IGNORECASE)
CREATE_RE = re.compile(r"\bCREATE\b", re.IGNORECASE)
CREATE_CONSTRAINT_RE = re.compile(r"\bCREATE\s+CONSTRAINT\b", re.IGNORECASE)


def contains_apoc(text: str) -> bool:
    """Detecta `apoc.` sem distincao de maiusculas e minusculas."""
    return APOC_RE.search(text) is not None


def strip_comments(text: str) -> str:
    """Remove comentarios `//` e `/* */`, respeitando literais entre aspas."""
    out = []
    i, n = 0, len(text)
    quote = None
    while i < n:
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
        elif ch in ("'", '"', "`"):
            quote = ch
            out.append(ch)
            i += 1
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


# --- Detector de apoc. sobre textos gerados ---------------------------------

_filler = st.text(max_size=40).filter(lambda s: not contains_apoc(s))


def _case_variant(draw_bools):
    return "".join(c.upper() if up else c for c, up in zip("apoc", draw_bools))


@given(
    prefix=_filler,
    suffix=_filler,
    flags=st.lists(st.booleans(), min_size=4, max_size=4),
)
def test_detector_flags_apoc_in_any_case_and_position(prefix, suffix, flags):
    text = f"{prefix}{_case_variant(flags)}.{suffix}"
    assert contains_apoc(text)


@given(text=st.text(max_size=200).filter(lambda s: "apoc." not in s.lower()))
def test_detector_has_no_false_positives(text):
    assert not contains_apoc(text)


# --- Varredura dos arquivos reais -------------------------------------------


def test_cypher_files_have_no_apoc(cypher_dir):
    files = sorted(cypher_dir.glob("*.cypher"))
    assert files, "nenhum script em cypher/"
    for f in files:
        assert not contains_apoc(f.read_text(encoding="utf-8")), f.name


def test_load_script_has_no_create_and_uses_merge(cypher_dir):
    code = strip_comments((cypher_dir / "02_load.cypher").read_text(encoding="utf-8"))
    assert CREATE_RE.search(code) is None
    assert re.search(r"\bMERGE\b", code, re.IGNORECASE)


def test_constraints_script_only_creates_constraints(cypher_dir):
    code = strip_comments(
        (cypher_dir / "01_constraints.cypher").read_text(encoding="utf-8")
    )
    creates = len(CREATE_RE.findall(code))
    assert creates == len(CREATE_CONSTRAINT_RE.findall(code))


def test_strip_comments_examples():
    src = "// CREATE x\nMERGE (n) /* CREATE */ SET n.t = 'CREATE // no'"
    code = strip_comments(src)
    assert "CREATE x" not in code
    assert "/* CREATE */" not in code
    assert "'CREATE // no'" in code
