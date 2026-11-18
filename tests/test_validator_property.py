"""Property 1: validador de dataset aceita se, e somente se, as regras do Requirement 5 valem."""

from hypothesis import given

from tests.helpers.generators import invalid_datasets, valid_datasets
from tests.helpers.validator import validate


# Feature: neo4j-uml-graph-portfolio, Property 1
# Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.8, 5.9
@given(valid_datasets())
def test_dataset_valido_nao_gera_erros(ds):
    assert validate(ds) == []


# Feature: neo4j-uml-graph-portfolio, Property 1
# Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.8, 5.9
@given(invalid_datasets())
def test_mutacao_invalida_e_rejeitada_com_a_regra_esperada(caso):
    ds, mutacao, regra = caso
    erros = validate(ds)
    assert erros, f"mutação {mutacao} não foi rejeitada"
    assert regra in {e.regra for e in erros}, (mutacao, erros)
    assert all(e.linha >= 1 for e in erros)
