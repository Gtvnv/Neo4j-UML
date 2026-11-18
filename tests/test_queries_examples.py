"""Testes de exemplo das consultas Q01-Q08 no dataset real."""

import re

import pytest

from tests.helpers.neo4j_fixture import CYPHER_DIR, QUERIES_FILE, load_queries, parse_param_defaults

pytestmark = pytest.mark.neo4j

CONTAGENS = (
    "CALL { MATCH (n) RETURN count(n) AS nos } "
    "CALL { MATCH ()-[r]->() RETURN count(r) AS rels } "
    "RETURN nos, rels"
)


@pytest.fixture()
def banco_real(neo4j_db):
    neo4j_db.reset()
    neo4j_db.clear_import()
    neo4j_db.copy_real_dataset()
    neo4j_db.run_script("01_constraints.cypher")
    neo4j_db.run_script("02_load.cypher")
    try:
        yield neo4j_db
    finally:
        neo4j_db.reset()


def test_q04_devolve_apenas_o_ciclo_de_servicos(banco_real):
    linhas = banco_real.run_query("Q04")
    assert len(linhas) == 1
    assert set(linhas[0]["ciclo"]) == {"OrderService", "PaymentService", "NotificationService"}
    assert len(linhas[0]["ciclo"]) == 3


def test_q05_devolve_apenas_payment_para_stripe_gateway(banco_real):
    linhas = banco_real.run_query("Q05")
    assert linhas == [{"origem": "Payment", "destino": "StripeGateway", "pacoteDestino": "infra"}]


def test_q03_stripe_gateway_alcanca_dependentes_transitivos(banco_real):
    linhas = banco_real.run_query("Q03", nome="StripeGateway")
    impactados = {r["impactado"] for r in linhas}
    assert {"Payment", "PaymentService", "NotificationService", "OrderService"} <= impactados
    assert "StripeGateway" not in impactados


@pytest.mark.parametrize("qid", sorted(
    q for q, t in load_queries().items() if re.search(r"\$\w+", t)
))
def test_consulta_parametrizada_sem_parametro_falha_e_nao_altera_grafo(banco_real, qid):
    antes = banco_real.run(CONTAGENS)
    with pytest.raises(Exception) as exc:
        banco_real.run_query(qid)
    msg = str(exc.value).lower()
    assert "parameter" in msg and ("missing" in msg or "expected" in msg), msg
    assert banco_real.run(CONTAGENS) == antes


def test_consultas_nao_tem_valor_literal_no_lugar_do_parametro():
    texto = (CYPHER_DIR / QUERIES_FILE).read_text(encoding="utf-8")
    defaults = parse_param_defaults(texto)
    assert set(defaults) == {"nome", "interface", "metodo", "pacote"}
    consultas = load_queries()
    assert len(consultas) == 8
    parametrizadas = {q: t for q, t in consultas.items() if re.search(r"\$\w+", t)}
    assert set(parametrizadas) == {"Q01", "Q02", "Q03", "Q07", "Q08"}
    for qid, corpo in parametrizadas.items():
        for nome, valor in defaults.items():
            assert not re.search(rf"""['"]{re.escape(str(valor))}['"]""", corpo), (
                f"{qid} contém o valor fixo de ${nome}"
            )
        # nenhum filtro de propriedade com literal textual
        assert not re.search(r"""\{\s*\w+\s*:\s*['"]""", corpo), f"{qid} filtra por literal"
        assert not re.search(r"""\.\w+\s*(=|<>)\s*['"]""", corpo), f"{qid} compara com literal"
