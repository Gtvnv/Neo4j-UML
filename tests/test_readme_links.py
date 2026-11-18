"""Feature: neo4j-uml-graph-portfolio, Property 16: Todo link de imagem do README resolve para um arquivo existente.

**Validates: Requirements 8.6**
"""

import re
import tempfile
from pathlib import Path, PurePosixPath

from hypothesis import given, strategies as st

REPO = Path(__file__).resolve().parent.parent
IMAGE_RE = re.compile(r"!\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)")
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def extract_image_links(markdown: str) -> list[str]:
    """Caminhos de `![alt](caminho)` fora de blocos de codigo (cercados e inline)."""
    links: list[str] = []
    fence: str | None = None
    for line in markdown.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0] * 3
                continue
            links.extend(IMAGE_RE.findall(INLINE_CODE_RE.sub("", line)))
        elif m and m.group(1).startswith(fence):
            fence = None
    return links


def is_valid_image_link(link: str, root: Path) -> bool:
    """Relativo, dentro de docs/images/ e apontando para um arquivo existente."""
    if not link or SCHEME_RE.match(link) or link.startswith(("/", "\\", "//", "#")):
        return False
    if "\\" in link:
        return False
    parts = PurePosixPath(link).parts
    if ".." in parts:
        return False
    if parts[:2] != ("docs", "images") or len(parts) < 3:
        return False
    return (root / link).is_file()


# --- Exemplos do extrator e do validador ---

def test_extractor_ignores_fenced_and_inline_code():
    md = (
        "![a](docs/images/a.png)\n"
        "```\n![b](docs/images/b.png)\n```\n"
        "~~~\n![c](docs/images/c.png)\n~~~\n"
        "`![d](docs/images/d.png)` e ![e](docs/images/e.png)\n"
    )
    assert extract_image_links(md) == ["docs/images/a.png", "docs/images/e.png"]


def test_validator_rejects_absolute_external_and_outside():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "docs" / "images").mkdir(parents=True)
        (root / "docs" / "images" / "ok.png").write_bytes(b"x")
        (root / "outside.png").write_bytes(b"x")
        assert is_valid_image_link("docs/images/ok.png", root)
        for bad in (
            "docs/images/missing.png",
            "/docs/images/ok.png",
            "C:/docs/images/ok.png",
            "https://example.com/docs/images/ok.png",
            "data:image/png;base64,AAAA",
            "docs/images/../../outside.png",
            "outside.png",
            "docs\\images\\ok.png",
        ):
            assert not is_valid_image_link(bad, root), bad


# --- Propriedade 16 ---

_name = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=12)


@given(
    existing=st.lists(_name, unique=True, max_size=5),
    missing=st.lists(_name, unique=True, max_size=5),
    bad=st.lists(
        st.sampled_from(
            ["/abs/x.png", "https://e.com/x.png", "http://e.com/x.png", "../x.png", "C:/x.png"]
        ),
        max_size=3,
    ),
    in_code=st.lists(_name, max_size=3),
)
def test_property_16_readme_image_links(existing, missing, bad, in_code):
    """Feature: neo4j-uml-graph-portfolio, Property 16"""
    missing = [m for m in missing if m not in existing]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "docs" / "images").mkdir(parents=True)
        for n in existing:
            (root / "docs" / "images" / f"{n}.png").write_bytes(b"x")
        lines = [f"![img {n}](docs/images/{n}.png)" for n in existing]
        lines += [f"![img {n}](docs/images/{n}.png)" for n in missing]
        lines += [f"![ruim]({b})" for b in bad]
        expected = [l.split("(", 1)[1][:-1] for l in lines]
        lines.append("```")
        lines += [f"![codigo](docs/images/{n}.png)" for n in in_code]
        lines.append("```")
        md = "\n\n".join(lines[: len(expected)]) + "\n" + "\n".join(lines[len(expected):]) + "\n"

        links = extract_image_links(md)
        assert links == expected  # acha todos, sem falso positivo em bloco de codigo
        for link in links:
            valid = is_valid_image_link(link, root)
            should = (
                link.startswith("docs/images/")
                and Path(link).stem in existing
                and link not in bad
            )
            assert valid == should


def test_real_readme_image_links_resolve():
    """README real: hoje sem imagens (vacuo); qualquer link futuro deve resolver."""
    text = (REPO / "README.md").read_text(encoding="utf-8")
    for link in extract_image_links(text):
        assert is_allowed_readme_image(link, REPO), f"link de imagem invalido: {link}"


SHIELDS_PREFIX = "https://img.shields.io/"


def is_allowed_readme_image(link: str, root: Path) -> bool:
    """Badge do shields.io (https, host exato) ou imagem local valida."""
    if link.startswith(SHIELDS_PREFIX) and len(link) > len(SHIELDS_PREFIX):
        return True
    return is_valid_image_link(link, root)


def test_readme_allows_only_shields_externally():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        assert is_allowed_readme_image("https://img.shields.io/badge/a-b-blue", root)
        for bad in (
            "https://example.com/badge.svg",
            "http://img.shields.io/badge/a-b-blue",
            "https://img.shields.io.evil.com/x.svg",
            "https://img.shields.io@evil.com/x.svg",
            "https://img.shields.io/",
        ):
            assert not is_allowed_readme_image(bad, root), bad
