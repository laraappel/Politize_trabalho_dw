"""Comandos de linha de comando: migrações e coleta de notícias."""
import os
from datetime import date
from pathlib import Path

import click
from sqlalchemy import text

from app.extensions import db


def _dir_migracoes() -> Path:
    return Path(os.getenv("MIGRATIONS_DIR", "/database/migrations"))


def _ordem_migracao(arquivo: Path):
    """Ordena pelo prefixo numérico. 003_dominio antecede 003_camara."""
    nome = arquivo.stem
    prefixo = nome.split("_", 1)[0]
    try:
        numero = int(prefixo)
    except ValueError:
        numero = 10_000
    desempate = 1 if nome == "003_camara" else 0
    return (numero, desempate, nome)


def register_cli(app):
    @app.cli.command("migrate")
    def migrate():
        """Aplica database/migrations/*.sql ainda não registradas em schema_migrations."""
        pasta = _dir_migracoes()
        if not pasta.is_dir():
            raise click.ClickException(f"Pasta de migrações não encontrada: {pasta}")
        aplicadas = {r[0] for r in db.session.execute(text("SELECT version FROM schema_migrations"))}
        for arquivo in sorted(pasta.glob("*.sql"), key=_ordem_migracao):
            versao = arquivo.stem
            if versao in aplicadas:
                click.echo(f"= {versao} (já aplicada)")
                continue
            db.session.connection().exec_driver_sql(arquivo.read_text(encoding="utf-8"))
            db.session.commit()
            click.echo(f"+ {versao} aplicada")
        from app.services.noticias.coleta import sincronizar_veiculos

        sincronizar_veiculos()
        click.echo("Fontes de notícias sincronizadas.")

    @app.cli.command("sincronizar-fontes")
    def sincronizar_fontes():
        """Atualiza a tabela veiculos com a base de autorização de cada fonte."""
        from app.services.noticias.coleta import sincronizar_veiculos

        for slug, v in sincronizar_veiculos().items():
            click.echo(f"{slug}: coleta_autorizada={v.coleta_autorizada}")

    @app.cli.command("coletar-noticias")
    @click.option("--fonte", "fonte", default=None, help="Slug da fonte (padrão: todas as autorizadas).")
    @click.option("--forcar", is_flag=True, help="Ignora o intervalo mínimo entre coletas.")
    def coletar_noticias(fonte, forcar):
        """Coleta metadados de notícias das fontes autorizadas."""
        from app.services.noticias.coleta import coletar_fonte
        from app.services.noticias.fontes import todas_as_fontes

        fontes = todas_as_fontes()
        alvos = [fonte] if fonte else [s for s, f in fontes.items() if f.autorizada]
        for slug in alvos:
            c = coletar_fonte(slug, forcar=forcar, fontes=fontes)
            click.echo(
                f"{slug}: {c.status} lidos={c.itens_lidos} novos={c.itens_novos} "
                f"atualizados={c.itens_atualizados} descartados={c.itens_descartados}"
                + (f" | {c.mensagem}" if c.mensagem else "")
            )

    @app.cli.command("importar-camara-inicial")
    @click.option("--ano-inicial", type=int, default=lambda: date.today().year, show_default="ano atual", help="Primeiro ano de despesas e proposições a importar.")
    @click.option("--ano-final", type=int, default=lambda: date.today().year, show_default="ano atual", help="Último ano de despesas e proposições a importar.")
    @click.option("--limite-deputados", type=click.IntRange(min=1), default=None, help="Limita deputados para teste controlado.")
    def importar_camara_inicial(ano_inicial, ano_final, limite_deputados):
        """Importa dados iniciais da Câmara. Execute manualmente, fora das requisições web."""
        if ano_inicial > ano_final:
            raise click.ClickException("ano-inicial não pode ser maior que ano-final.")
        from app.services.camara.sincronizacao import CamaraSyncService
        try:
            resultados = CamaraSyncService().importar_inicial(ano_inicial, ano_final, limite_deputados)
            for entidade, (lidos, novos, atualizados) in resultados.items():
                click.echo(f"{entidade}: lidos={lidos} novos={novos} atualizados={atualizados}")
        except Exception as exc:
            raise click.ClickException(f"Importação inicial da Câmara falhou: {exc}") from exc

    @app.cli.command("atualizar-camara")
    @click.option("--ano", type=int, default=lambda: date.today().year, show_default="ano atual", help="Ano a consultar para despesas e proposições.")
    @click.option("--limite-deputados", type=click.IntRange(min=1), default=None, help="Limita deputados para teste controlado.")
    def atualizar_camara(ano, limite_deputados):
        """Atualiza os registros já importados e incorpora novos dados da Câmara."""
        from app.services.camara.sincronizacao import CamaraSyncService
        try:
            resultados = CamaraSyncService().atualizar(ano, limite_deputados)
            for entidade, (lidos, novos, atualizados) in resultados.items():
                click.echo(f"{entidade}: lidos={lidos} novos={novos} atualizados={atualizados}")
        except Exception as exc:
            raise click.ClickException(f"Atualização da Câmara falhou: {exc}") from exc

    @app.cli.command("importar-dados")
    @click.option("--arquivo", required=True, type=click.Path(exists=True, dir_okay=False))
    def importar_dados(arquivo):
        """Importa um pacote JSON de forma idempotente (não cria duplicatas)."""
        from app.services.importacao import importar_arquivo

        resumo = importar_arquivo(arquivo)
        click.echo(f"políticos novos={resumo['politicos_novos']} existentes={resumo['politicos_existentes']}")
        click.echo(
            f"mandatos novos={resumo['mandatos_novos']} projetos novos={resumo['projetos_novos']} "
            f"votações novas={resumo['votacoes_novas']} despesas novas={resumo['despesas_novas']} "
            f"notícias novas={resumo['noticias_novas']}"
        )
        if resumo.get("aviso"):
            click.echo(resumo["aviso"])