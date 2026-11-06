"""Comandos de linha de comando: migrações e coleta de notícias."""
import os
from pathlib import Path

import click
from sqlalchemy import text

from app.extensions import db


def _dir_migracoes() -> Path:
    return Path(os.getenv("MIGRATIONS_DIR", "/database/migrations"))


def register_cli(app):
    @app.cli.command("migrate")
    def migrate():
        """Aplica database/migrations/*.sql ainda não registradas em schema_migrations."""
        pasta = _dir_migracoes()
        if not pasta.is_dir():
            raise click.ClickException(f"Pasta de migrações não encontrada: {pasta}")
        aplicadas = {r[0] for r in db.session.execute(text("SELECT version FROM schema_migrations"))}
        for arquivo in sorted(pasta.glob("*.sql")):
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
