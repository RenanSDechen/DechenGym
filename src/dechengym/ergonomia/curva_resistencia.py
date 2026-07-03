"""
Curva de resistência x curva de força.
======================================

Ferramentas para acessar a curva de força humana de um grupo muscular e
avaliar o quão bem a resistência da máquina (perfil de torque ao longo do
movimento) acompanha essa curva — o que define se a solicitação muscular
é adequada do início ao fim do exercício.
"""

from __future__ import annotations

from typing import Any, Sequence

from dechengym.data.curva_forca_db import (
    AMOSTRAS_PCT,
    CURVAS_FORCA,
    grupos_disponiveis,
)


def get_curva_forca(grupo_muscular: str) -> dict[str, Any]:
    """Retorna a curva de força humana normalizada de um grupo muscular.

    Returns
    -------
    dict
        ``{"grupo_muscular", "tipo", "amostras_pct", "perfil", "descricao"}``.

    Raises
    ------
    KeyError
        Se o grupo muscular não existir.
    """
    if grupo_muscular not in CURVAS_FORCA:
        raise KeyError(
            f"Grupo muscular '{grupo_muscular}' invalido. Use: {grupos_disponiveis()}"
        )
    dados = CURVAS_FORCA[grupo_muscular]
    return {
        "grupo_muscular": grupo_muscular,
        "tipo": dados["tipo"],
        "amostras_pct": list(AMOSTRAS_PCT),
        "perfil": list(dados["perfil"]),
        "descricao": dados["descricao"],
    }


def gerar_perfil_resistencia_alvo(
    grupo_muscular: str, carga_pico_kg: float
) -> dict[str, Any]:
    """Gera o perfil de resistência-alvo que acompanha a curva de força.

    Para manter a intensidade relativa constante, a resistência ideal em
    cada ponto do movimento é proporcional à capacidade de força naquele
    ponto: ``resistencia(%) = carga_pico × fator_forca(%)``.

    Este perfil é o alvo que a geometria do braço/came deve reproduzir.

    Parameters
    ----------
    grupo_muscular:
        Grupo cuja curva de força será seguida.
    carga_pico_kg:
        Carga (kg) correspondente ao ponto de maior força (fator 1.0).

    Returns
    -------
    dict
        ``{"grupo_muscular", "amostras_pct", "resistencia_alvo_kg"}``.
    """
    if carga_pico_kg < 0:
        raise ValueError("carga_pico_kg nao pode ser negativa.")
    curva = get_curva_forca(grupo_muscular)
    alvo = [round(carga_pico_kg * f, 2) for f in curva["perfil"]]
    return {
        "grupo_muscular": grupo_muscular,
        "amostras_pct": curva["amostras_pct"],
        "resistencia_alvo_kg": alvo,
    }


def _normalizar(valores: Sequence[float]) -> list[float]:
    """Normaliza uma sequência para o intervalo [0, 1] pelo valor máximo."""
    pico = max(valores)
    if pico <= 0:
        raise ValueError("Perfil de resistencia deve ter ao menos um valor > 0.")
    return [v / pico for v in valores]


def avaliar_curva_resistencia(
    perfil_maquina: Sequence[float], grupo_muscular: str
) -> dict[str, Any]:
    """Avalia o casamento entre a resistência da máquina e a curva de força.

    Normaliza ambos os perfis (por seus picos) e mede o desvio ponto a ponto.
    Retorna uma pontuação de 0 a 100 (100 = casamento perfeito) e a lista de
    pontos com maior descasamento, úteis para orientar o ajuste da geometria.

    Parameters
    ----------
    perfil_maquina:
        Torque/resistência da máquina amostrado nos mesmos pontos da curva
        de força (0%, 25%, 50%, 75%, 100% do movimento). Pode estar em
        qualquer unidade — a comparação é feita pela **forma** (normalizada).
    grupo_muscular:
        Grupo muscular de referência.

    Returns
    -------
    dict
        ``{"grupo_muscular", "pontuacao", "erro_medio", "perfil_humano_norm",
        "perfil_maquina_norm", "pior_ponto_pct", "recomendacao"}``.
    """
    curva = get_curva_forca(grupo_muscular)
    humano = curva["perfil"]

    if len(perfil_maquina) != len(humano):
        raise ValueError(
            f"perfil_maquina deve ter {len(humano)} amostras "
            f"(recebido {len(perfil_maquina)})."
        )

    hn = _normalizar(humano)
    mn = _normalizar(perfil_maquina)

    desvios = [abs(h - m) for h, m in zip(hn, mn)]
    erro_medio = sum(desvios) / len(desvios)
    pontuacao = round(max(0.0, 100.0 * (1.0 - erro_medio)), 1)

    idx_pior = max(range(len(desvios)), key=lambda i: desvios[i])
    pior_pct = curva["amostras_pct"][idx_pior]

    if pontuacao >= 90:
        recomendacao = "Excelente casamento; geometria adequada."
    elif pontuacao >= 75:
        recomendacao = (
            f"Bom casamento. Ajuste fino em ~{pior_pct}% do movimento pode melhorar."
        )
    else:
        alvo = "aumentar" if mn[idx_pior] < hn[idx_pior] else "reduzir"
        recomendacao = (
            f"Casamento fraco. {alvo.capitalize()} a resistencia em ~{pior_pct}% "
            f"do movimento (ajustar raio do came / comprimento efetivo da alavanca)."
        )

    return {
        "grupo_muscular": grupo_muscular,
        "tipo_curva": curva["tipo"],
        "pontuacao": pontuacao,
        "erro_medio": round(erro_medio, 4),
        "amostras_pct": curva["amostras_pct"],
        "perfil_humano_norm": [round(v, 3) for v in hn],
        "perfil_maquina_norm": [round(v, 3) for v in mn],
        "pior_ponto_pct": pior_pct,
        "recomendacao": recomendacao,
    }
