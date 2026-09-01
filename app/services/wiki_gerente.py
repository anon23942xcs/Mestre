"""Aplicação defensiva do patch da Wiki, sem chamadas próprias de IA."""
from app.models.estado import EstadoCompleto
from app.models.ficha import FichaMundo
from app.storage import ficha_repositorio


def aplicar_patch_wiki(estado: EstadoCompleto, patch: object) -> None:
    if not isinstance(patch, dict):
        return
    campanha_id = estado.campanha_id
    escopo = f"campanha_{campanha_id}"
    fichas = {f.id: f for f in ficha_repositorio.listar(escopo)}

    for atualizacao in patch.get("fichas_atualizadas") or []:
        if not isinstance(atualizacao, dict):
            continue
        ficha = fichas.get(atualizacao.get("id"))
        if not ficha:
            continue
        campos = atualizacao.get("campos")
        if isinstance(campos, dict):
            ficha.campos.update({str(chave): valor for chave, valor in campos.items()})
        append = atualizacao.get("conteudo_append")
        if isinstance(append, str) and append.strip():
            ficha.conteudo = (ficha.conteudo + "\n\n" + append.strip()).strip()
        ficha_repositorio.salvar(escopo, ficha)

    nova = patch.get("ficha_nova")
    if isinstance(nova, dict):
        try:
            dados = dict(nova)
            dados["id"] = dados.get("id") if isinstance(dados.get("id"), str) else ficha_repositorio.novo_id()
            if dados["id"] in fichas:
                dados["id"] = ficha_repositorio.novo_id()
            ficha = FichaMundo(**dados)
            ficha_repositorio.salvar(escopo, ficha)
            fichas[ficha.id] = ficha
        except Exception:
            pass

    for chave, adicionar in (("relacao_adicionada", True), ("relacao_removida", False)):
        for relacao in patch.get(chave) or []:
            if not isinstance(relacao, dict):
                continue
            origem = fichas.get(relacao.get("origem"))
            tipo = relacao.get("tipo_relacao")
            destino = relacao.get("destino")
            if not origem or not isinstance(tipo, str) or not isinstance(destino, str):
                continue
            destinos = origem.relacoes.setdefault(tipo, [])
            if adicionar and destino not in destinos:
                destinos.append(destino)
            elif not adicionar and destino in destinos:
                destinos.remove(destino)
                if not destinos:
                    origem.relacoes.pop(tipo, None)
            else:
                continue
            ficha_repositorio.salvar(escopo, origem)
