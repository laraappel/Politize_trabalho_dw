from app.services.noticias.fontes.agencia_brasil import AgenciaBrasil
from app.services.noticias.fontes.base import FonteNaoAutorizada, FonteNoticias
from app.services.noticias.fontes.nao_autorizadas import CnnBrasil, FolhaDeSPaulo, G1


def todas_as_fontes() -> dict[str, FonteNoticias]:
    fontes = [AgenciaBrasil(), G1(), CnnBrasil(), FolhaDeSPaulo()]
    return {f.slug: f for f in fontes}


__all__ = ["todas_as_fontes", "FonteNoticias", "FonteNaoAutorizada"]
