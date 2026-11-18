"""Property 15: nenhum arquivo, nome ou metadado contem o termo proibido.

**Validates: Requirements 12.1**

O padrao e montado por concatenacao de fragmentos, para que este arquivo
nao contenha o termo literalmente.
"""
import re
import struct
import zlib
from pathlib import Path

from hypothesis import given, settings, strategies as st

RAIZ = Path(__file__).resolve().parent.parent
EXCLUIDOS = {".git", ".kiro", ".pytest_cache", ".hypothesis", "__pycache__", ".venv"}

# Fragmentos: sigla de 3 letras (palavra isolada) e nome completo da organizacao.
_SIGLA = "d" + "i" + "o"
_NOME = ["dig" + "ital", "inno" + "vation", "o" + "ne"]
_FIM_PALAVRA = r"(?<![^\W_])" + _SIGLA + r"(?![^\W_])"
_NOME_COMPLETO = r"(?<![^\W_])" + r"[\W_]+".join(_NOME) + r"(?![^\W_])"
PADRAO = re.compile(_FIM_PALAVRA + "|" + _NOME_COMPLETO, re.IGNORECASE)


def contem_termo(texto: str) -> bool:
    return PADRAO.search(texto) is not None


# ---------------------------------------------------------------- detector
_SEPARADORES = st.sampled_from([" ", "\n", "\t", ".", ",", "-", "_", "/", "(", ")", "\"", ""])
_ALEATORIO = st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=30)


def _caixa(texto: str, bits: list) -> str:
    return "".join(c.upper() if bits[i % len(bits)] else c.lower() for i, c in enumerate(texto))


def _sem_letras_digitos(s: str) -> str:
    return "".join(c for c in s if not c.isalnum())


@given(
    prefixo=_ALEATORIO, sufixo=_ALEATORIO,
    bits=st.lists(st.booleans(), min_size=1, max_size=5),
    sep_a=_SEPARADORES, sep_b=_SEPARADORES,
)
@settings(max_examples=100)
def test_detector_acusa_sigla_isolada_em_qualquer_caixa(prefixo, sufixo, bits, sep_a, sep_b):
    # Garante fronteira de palavra: separador nao alfanumerico (ou vazio) junto de contexto sem alfanumericos.
    esq = _sem_letras_digitos(prefixo) + (sep_a or " ")
    dir_ = (sep_b or " ") + _sem_letras_digitos(sufixo)
    assert contem_termo(esq + _caixa(_SIGLA, bits) + dir_)


@given(
    bits=st.lists(st.booleans(), min_size=1, max_size=5),
    sep=st.sampled_from([" ", "  ", "\n", "-", "_"]),
)
@settings(max_examples=50)
def test_detector_acusa_nome_completo_em_qualquer_caixa(bits, sep):
    texto = "x " + sep.join(_caixa(p, bits) for p in _NOME) + " y"
    assert contem_termo(texto)


@given(
    antes=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", max_size=6),
    depois=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", max_size=6),
)
@settings(max_examples=100)
def test_detector_ignora_palavras_que_apenas_contem_a_sigla(antes, depois):
    if not antes and not depois:
        return
    assert not contem_termo(antes + _SIGLA + depois)


def test_detector_ignora_palavras_comuns_em_portugues():
    for palavra in ("ra" + _SIGLA, "estu" + _SIGLA, "me" + _SIGLA + "s", "audi" + "o", "r" + _SIGLA):
        assert not contem_termo(f"texto {palavra} comum"), palavra


# ---------------------------------------------------------- varredura do repo
def _arquivos_do_repo():
    for caminho in RAIZ.rglob("*"):
        rel = caminho.relative_to(RAIZ)
        if any(parte in EXCLUIDOS for parte in rel.parts):
            continue
        if caminho.is_file():
            yield caminho, rel


def _campos_texto_png(dados: bytes):
    """Extrai textos de tEXt/zTXt/iTXt e bytes de eXIf (inclui XMP em iTXt)."""
    campos = []
    if not dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return campos
    pos = 8
    while pos + 8 <= len(dados):
        tamanho, tipo = struct.unpack(">I4s", dados[pos:pos + 8])
        corpo = dados[pos + 8:pos + 8 + tamanho]
        pos += 12 + tamanho
        if tipo == b"tEXt":
            campos.append(corpo.decode("latin-1"))
        elif tipo == b"zTXt":
            chave, _, resto = corpo.partition(b"\x00")
            campos.append(chave.decode("latin-1"))
            try:
                campos.append(zlib.decompress(resto[1:]).decode("utf-8", "replace"))
            except zlib.error:
                campos.append(resto.decode("latin-1"))
        elif tipo == b"iTXt":
            chave, _, resto = corpo.partition(b"\x00")
            campos.append(chave.decode("utf-8", "replace"))
            comprimido, metodo = resto[0:1], resto[1:2]
            resto = resto[2:]
            _, _, resto = resto.partition(b"\x00")  # idioma
            _, _, texto = resto.partition(b"\x00")  # chave traduzida
            if comprimido == b"\x01":
                try:
                    texto = zlib.decompress(texto)
                except zlib.error:
                    pass
            campos.append(texto.decode("utf-8", "replace"))
        elif tipo == b"eXIf":
            campos.append(corpo.decode("latin-1"))
            campos.append(corpo.decode("utf-16-le", "replace"))
        if tipo == b"IEND":
            break
    return campos


def _campos_metadados_binarios(dados: bytes):
    """Para imagens nao PNG: procura pacotes XMP e texto EXIF em bytes brutos."""
    campos = []
    for m in re.finditer(rb"<\?xpacket.*?<\?xpacket end[^>]*>", dados, re.S):
        campos.append(m.group(0).decode("utf-8", "replace"))
    if dados.startswith(b"\xff\xd8") or dados[:4] in (b"II*\x00", b"MM\x00*"):
        campos.append(dados.decode("latin-1"))
    return campos


def test_nenhum_arquivo_nome_ou_metadado_contem_o_termo():
    violacoes = []
    for caminho, rel in _arquivos_do_repo():
        # Nomes de arquivo e de pastas
        for parte in rel.parts:
            if contem_termo(parte):
                violacoes.append(f"nome: {rel}")
                break
        dados = caminho.read_bytes()
        # Conteudo textual
        try:
            texto = dados.decode("utf-8")
        except UnicodeDecodeError:
            texto = None
        if texto is not None and contem_termo(texto):
            violacoes.append(f"conteudo: {rel}")
        # Metadados de imagem
        campos = _campos_texto_png(dados) + (
            _campos_metadados_binarios(dados) if texto is None and not dados.startswith(b"\x89PNG") else []
        )
        for campo in campos:
            if contem_termo(campo):
                violacoes.append(f"metadado de imagem: {rel}")
                break
    assert not violacoes, "Termo proibido encontrado em:\n" + "\n".join(violacoes)
