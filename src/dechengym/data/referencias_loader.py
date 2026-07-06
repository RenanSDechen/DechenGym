"""
Carregador da base de desenhos extraídos (pacote completo da fábrica).
======================================================================

Os agentes de extração gravam em ``dechengym/data/referencias/*.json`` um
objeto por prancha lida (peça, função, material, seções, cotas, furos, BOM).
Este módulo indexa esses arquivos e expõe consultas por projeto — a camada
de dados que alimenta o gerador e as tools de referência.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DIR_REFERENCIAS = Path(__file__).parent / "referencias"


@lru_cache(maxsize=1)
def _carregar_tudo() -> list[dict[str, Any]]:
    """Carrega todos os desenhos extraídos (cacheado)."""
    desenhos: list[dict[str, Any]] = []
    if not _DIR_REFERENCIAS.is_dir():
        return desenhos
    for arq in sorted(_DIR_REFERENCIAS.glob("*.json")):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(dados, list):
            for d in dados:
                if isinstance(d, dict):
                    d.setdefault("_fonte_json", arq.name)
                    desenhos.append(d)
    return desenhos


def listar_projetos_extraidos() -> dict[str, Any]:
    """Resumo da base extraída: projetos, nº de desenhos e arquivos-fonte."""
    projetos: dict[str, dict[str, Any]] = {}
    for d in _carregar_tudo():
        p = str(d.get("projeto", "desconhecido"))
        info = projetos.setdefault(p, {"desenhos": 0, "fontes": set()})
        info["desenhos"] += 1
        info["fontes"].add(d["_fonte_json"])
    return {
        "total_projetos": len(projetos),
        "total_desenhos": sum(v["desenhos"] for v in projetos.values()),
        "projetos": {k: {"desenhos": v["desenhos"],
                         "fontes": sorted(v["fontes"])}
                     for k, v in sorted(projetos.items())},
    }


def get_desenhos_projeto(projeto: str) -> list[dict[str, Any]]:
    """Todos os desenhos extraídos de um projeto (ex.: ``"remada"``)."""
    achados = [d for d in _carregar_tudo()
               if str(d.get("projeto", "")).lower() == projeto.lower()]
    if not achados:
        disponiveis = ", ".join(sorted(
            {str(d.get("projeto", "")) for d in _carregar_tudo()}))
        raise ValueError(f"Projeto '{projeto}' não encontrado na base "
                         f"extraída. Disponíveis: {disponiveis or '(vazia)'}")
    return achados


def recarregar() -> None:
    """Limpa o cache (após novos JSONs serem gravados)."""
    _carregar_tudo.cache_clear()
