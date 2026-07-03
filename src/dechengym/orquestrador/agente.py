"""
Ponto de entrada do orquestrador.
=================================

:func:`orquestrar` une a **interpretação do briefing** (camada de LLM
plugável) ao **pipeline determinístico** de projeto, opcionalmente gravando
os artefatos em disco.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dechengym.orquestrador.adapters import AdaptadorLLM, adaptador_padrao
from dechengym.orquestrador.pipeline import RequisicaoProjeto, projetar_maquina


def orquestrar(
    briefing: str,
    adaptador: AdaptadorLLM | None = None,
    diretorio_saida: str | Path | None = None,
    **sobrescritas: Any,
) -> dict[str, Any]:
    """Projeta uma máquina a partir de um briefing em linguagem natural.

    Parameters
    ----------
    briefing:
        Texto livre descrevendo o equipamento desejado (ex.:
        ``"quero uma rosca de biceps para 40 kg, publico feminino P50"``).
    adaptador:
        Interpretador de briefing. Se omitido, usa
        :func:`~dechengym.orquestrador.adapters.adaptador_padrao`
        (Anthropic quando há credencial; senão, regras).
    diretorio_saida:
        Se informado, grava ``.scad``/``.svg``/``.json`` do projeto.
    **sobrescritas:
        Campos de :class:`RequisicaoProjeto` para forçar/complementar o que
        foi interpretado (ex.: ``perfil="60x60"``, ``carga_kg=120``).

    Returns
    -------
    dict
        ``{"adaptador", "requisicao", "projeto"}``.
    """
    adaptador = adaptador or adaptador_padrao()
    requisicao = adaptador.interpretar(briefing)

    if sobrescritas:
        requisicao = RequisicaoProjeto(**{**requisicao.to_dict(), **sobrescritas})

    projeto = projetar_maquina(requisicao)

    if diretorio_saida is not None:
        _gravar_artefatos(projeto, diretorio_saida)

    return {
        "adaptador": adaptador.nome,
        "requisicao": requisicao.to_dict(),
        "projeto": projeto,
    }


def _gravar_artefatos(projeto: dict[str, Any], diretorio_saida: str | Path) -> list[str]:
    """Grava os artefatos do projeto e retorna os caminhos criados."""
    out = Path(diretorio_saida)
    out.mkdir(parents=True, exist_ok=True)
    nome = projeto["requisicao"]["exercicio"]

    caminhos: dict[str, str] = {
        f"{nome}.scad": projeto["geometria"]["openscad"],
        f"{nome}_preview.svg": projeto["imagem"]["preview_svg"],
        f"came_{nome}.scad": projeto["came"]["openscad"],
        f"came_{nome}.svg": projeto["came"]["svg"],
        f"{nome}_memorial.json": json.dumps(
            projeto["geometria"]["memorial"], indent=2, ensure_ascii=False
        ),
        f"{nome}_projeto.json": json.dumps(
            {
                "requisicao": projeto["requisicao"],
                "aprovado": projeto["aprovado"],
                "resumo": projeto["resumo"],
                "estrutura": projeto["estrutura"],
                "came_avaliacao": projeto["came"]["avaliacao"],
                "prompt_imagem": projeto["imagem"]["prompt_produto"],
            },
            indent=2,
            ensure_ascii=False,
        ),
    }

    criados = []
    for arquivo, conteudo in caminhos.items():
        caminho = out / arquivo
        caminho.write_text(conteudo, encoding="utf-8")
        criados.append(str(caminho))
    return criados
