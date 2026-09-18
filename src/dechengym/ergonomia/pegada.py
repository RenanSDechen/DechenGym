"""
Padrão de pegada (empunhadura).
===============================

Ferramentas para especificar a interface mão–máquina:

- :func:`get_padrao_pegada`     — descreve orientação do punho e ênfase.
- :func:`dimensionar_pega`      — diâmetro da pega a partir do comprimento
  da mão e do objetivo (conforto/força/precisão).
- :func:`calcular_largura_pegada` — distância entre pegas a partir da
  largura biacromial.
"""

from __future__ import annotations

from typing import Any

from dechengym.data.pegada_db import (
    DIAMETRO_PEGA,
    LARGURAS_PEGADA,
    ORIENTACOES_PUNHO,
    larguras_disponiveis,
    objetivos_pega_disponiveis,
    orientacoes_disponiveis,
)
from dechengym.ergonomia.antropometria import get_antropometria


def get_padrao_pegada(orientacao: str) -> dict[str, Any]:
    """Descreve uma orientação de punho (pronada/supinada/neutra/mista).

    Returns
    -------
    dict
        ``{"orientacao", "descricao", "angulo_antebraco_graus", "enfase"}``.

    Raises
    ------
    KeyError
        Se a orientação não existir.
    """
    if orientacao not in ORIENTACOES_PUNHO:
        raise KeyError(
            f"Orientacao '{orientacao}' invalida. Use: {orientacoes_disponiveis()}"
        )
    dados = ORIENTACOES_PUNHO[orientacao]
    return {"orientacao": orientacao, **dados}


def dimensionar_pega(
    objetivo: str = "conforto",
    percentil: float = 50,
    sexo: str = "masculino",
    comprimento_mao_mm: float | None = None,
) -> dict[str, Any]:
    """Calcula o diâmetro recomendado da pega cilíndrica.

    O diâmetro é proporcional ao comprimento da mão, conforme o objetivo
    (ver :data:`dechengym.data.pegada_db.DIAMETRO_PEGA`), com *clamp* nos
    limites de sanidade. Se ``comprimento_mao_mm`` for informado, ele tem
    prioridade sobre percentil/sexo.

    Parameters
    ----------
    objetivo:
        ``"conforto"`` (padrão), ``"forca_preensao"`` ou ``"precisao"``.
    percentil, sexo:
        Usados para obter o comprimento da mão se ele não for informado.
    comprimento_mao_mm:
        Comprimento da mão em mm (opcional; sobrepõe percentil/sexo).

    Returns
    -------
    dict
        ``{"objetivo", "comprimento_mao_mm", "diametro_ideal_mm",
        "diametro_recomendado_mm", "faixa_mm", "aplicado_clamp"}``.

    Examples
    --------
    >>> spec = dimensionar_pega("conforto", 50, "masculino")
    >>> 28.0 <= spec["diametro_recomendado_mm"] <= 45.0
    True
    """
    if objetivo not in DIAMETRO_PEGA:
        raise KeyError(
            f"Objetivo '{objetivo}' invalido. Use: {objetivos_pega_disponiveis()}"
        )

    if comprimento_mao_mm is None:
        comprimento_mao_mm = get_antropometria("comprimento_mao", percentil, sexo)
    elif comprimento_mao_mm <= 0:
        raise ValueError("comprimento_mao_mm deve ser positivo.")

    cfg = DIAMETRO_PEGA[objetivo]
    ideal = comprimento_mao_mm * cfg["fator_comprimento_mao"]

    minimo, maximo = cfg["faixa_mm"]
    recomendado = max(minimo, min(maximo, ideal))
    aplicado_clamp = recomendado != ideal

    return {
        "objetivo": objetivo,
        "descricao": cfg["descricao"],
        "comprimento_mao_mm": round(comprimento_mao_mm, 1),
        "diametro_ideal_mm": round(ideal, 1),
        "diametro_recomendado_mm": round(recomendado, 1),
        "faixa_mm": list(cfg["faixa_mm"]),
        "aplicado_clamp": aplicado_clamp,
    }


def calcular_largura_pegada(
    largura: str = "media",
    percentil: float = 50,
    sexo: str = "masculino",
    largura_biacromial_mm: float | None = None,
) -> dict[str, Any]:
    """Calcula a distância entre pegas a partir da largura biacromial.

    Parameters
    ----------
    largura:
        ``"fechada"``, ``"media"`` (padrão) ou ``"aberta"``.
    percentil, sexo:
        Usados para obter a largura biacromial se ela não for informada.
    largura_biacromial_mm:
        Largura biacromial em mm (opcional; sobrepõe percentil/sexo).

    Returns
    -------
    dict
        ``{"largura", "fator_biacromial", "largura_biacromial_mm",
        "distancia_entre_pegas_mm", "observacao"}``.
    """
    if largura not in LARGURAS_PEGADA:
        raise KeyError(
            f"Largura '{largura}' invalida. Use: {larguras_disponiveis()}"
        )

    if largura_biacromial_mm is None:
        largura_biacromial_mm = get_antropometria("largura_biacromial", percentil, sexo)
    elif largura_biacromial_mm <= 0:
        raise ValueError("largura_biacromial_mm deve ser positivo.")

    cfg = LARGURAS_PEGADA[largura]
    distancia = largura_biacromial_mm * cfg["fator_biacromial"]

    return {
        "largura": largura,
        "descricao": cfg["descricao"],
        "fator_biacromial": cfg["fator_biacromial"],
        "largura_biacromial_mm": round(largura_biacromial_mm, 1),
        "distancia_entre_pegas_mm": round(distancia, 1),
        "observacao": cfg["observacao"],
    }
