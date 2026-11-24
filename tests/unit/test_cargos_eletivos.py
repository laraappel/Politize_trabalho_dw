from app.adapters.senado import SenadoClient
from app.models.cargo_eletivo import CargoEletivo


def test_modelo_cargo_eletivo():
    assert CargoEletivo.__tablename__ == "cargos_eletivos"


def test_cliente_senado_possui_fonte_oficial():
    cliente = SenadoClient()
    assert "legis.senado.leg.br/dadosabertos" in cliente.BASE_URL
