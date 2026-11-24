from pathlib import Path

from app.models.dominios_eleitorais_transparencia import (
    Candidatura,
    PatrimonioDeclarado,
    ProjetoCoautoria,
    PropostaCampanha,
    Remuneracao,
)


def test_modelos_novos_estao_registrados():
    assert Candidatura.__tablename__ == "candidaturas"
    assert PropostaCampanha.__tablename__ == "propostas_campanha"
    assert ProjetoCoautoria.__tablename__ == "projeto_coautorias"
    assert Remuneracao.__tablename__ == "remuneracoes"
    assert PatrimonioDeclarado.__tablename__ == "patrimonio_declarado"


def test_migracao_cria_tabelas_sem_remover_existentes():
    candidatos = (
        Path("/database/migrations/009_dominios_eleitorais_transparencia.sql"),
        Path(__file__).resolve().parents[2] / "database/migrations/009_dominios_eleitorais_transparencia.sql",
    )
    caminho = next((item for item in candidatos if item.exists()), None)
    assert caminho is not None
    sql = caminho.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS candidaturas" in sql
    assert "CREATE TABLE IF NOT EXISTS propostas_campanha" in sql
    assert "CREATE TABLE IF NOT EXISTS projeto_coautorias" in sql
    assert "CREATE TABLE IF NOT EXISTS remuneracoes" in sql
    assert "CREATE TABLE IF NOT EXISTS patrimonio_declarado" in sql
    assert "DROP TABLE" not in sql
    assert "TRUNCATE" not in sql


def test_rota_nova_nao_usa_namespace_de_partidos_camara():
    candidatos = (
        Path("/app/app/routes/dominios_eleitorais.py"),
        Path(__file__).resolve().parents[2] / "backend/app/routes/dominios_eleitorais.py",
    )
    caminho = next((item for item in candidatos if item.exists()), None)
    assert caminho is not None
    codigo = caminho.read_text(encoding="utf-8")

    assert '"/partidos-cadastrados"' in codigo
    assert '"/politicos/<int:politico_id>/candidaturas"' in codigo
    assert '"/politicos/<int:politico_id>/remuneracoes"' in codigo
    assert '"/politicos/<int:politico_id>/patrimonio"' in codigo
