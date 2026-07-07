"""
Antropometria e faixas de ajuste.
=================================

Ferramentas para consultar dimensões corporais por percentil/sexo e para
dimensionar o **curso de regulagem** de componentes ajustáveis (assento,
encosto, braços, pegas) de modo a acomodar o envelope P5–P95.
"""

from __future__ import annotations

from typing import Any

from dechengym.data.antropometria_db import (
    DADOS,
    MEDIDAS,
    PERCENTIS_ANCORA,
    medidas_disponiveis,
    sexos_disponiveis,
)


def _interp_percentil(pontos: dict[int, float], percentil: float) -> float:
    """Interpola linearmente o valor de uma medida para um percentil.

    Usa os percentis-âncora (5, 50, 95). Fora do intervalo [5, 95] faz
    *clamp* nos extremos disponíveis (não extrapola).
    """
    ancoras = sorted(pontos.keys())
    if percentil <= ancoras[0]:
        return float(pontos[ancoras[0]])
    if percentil >= ancoras[-1]:
        return float(pontos[ancoras[-1]])

    # Encontra o par de âncoras que cerca o percentil e interpola.
    for menor, maior in zip(ancoras, ancoras[1:]):
        if menor <= percentil <= maior:
            frac = (percentil - menor) / (maior - menor)
            return float(pontos[menor] + frac * (pontos[maior] - pontos[menor]))
    return float(pontos[ancoras[-1]])  # inalcançável; segurança


def get_antropometria(
    medida: str, percentil: float = 50, sexo: str = "masculino"
) -> float:
    """Retorna uma dimensão corporal (mm) por medida, percentil e sexo.

    Parameters
    ----------
    medida:
        Chave da medida (ver :data:`dechengym.data.antropometria_db.MEDIDAS`),
        ex.: ``"altura_poplitea"``, ``"comprimento_mao"``.
    percentil:
        Percentil desejado (5–95). Valores intermediários são interpolados
        linearmente entre os percentis-âncora (5/50/95).
    sexo:
        ``"masculino"`` ou ``"feminino"``.

    Returns
    -------
    float
        Valor da medida em milímetros.

    Raises
    ------
    KeyError
        Se a medida ou o sexo não existirem.

    Examples
    --------
    >>> get_antropometria("altura_poplitea", 50, "masculino")
    440.0
    """
    if sexo not in DADOS:
        raise KeyError(f"Sexo '{sexo}' invalido. Use: {sexos_disponiveis()}")
    if medida not in DADOS[sexo]:
        raise KeyError(f"Medida '{medida}' invalida. Use: {medidas_disponiveis()}")

    return _interp_percentil(DADOS[sexo][medida], percentil)


def calcular_faixa_ajuste(
    medida: str,
    percentil_min: float = 5,
    percentil_max: float = 95,
    sexo: str = "ambos",
    folga_mm: float = 0.0,
) -> dict[str, Any]:
    """Dimensiona o curso de regulagem de um componente ajustável.

    Para acomodar o maior número de usuários, um componente deve regular do
    menor usuário relevante (tipicamente mulher P5) ao maior (homem P95). A
    função retorna os limites e o **curso** (amplitude de regulagem).

    Parameters
    ----------
    medida:
        Medida antropométrica de referência do componente.
    percentil_min, percentil_max:
        Percentis que definem os extremos do envelope (padrão 5 e 95).
    sexo:
        ``"masculino"``, ``"feminino"`` ou ``"ambos"``. Em ``"ambos"``, o
        mínimo e o máximo são tomados como o **menor** e o **maior** valor
        entre os dois sexos (não se assume que o homem é sempre o maior —
        para a largura do quadril, por exemplo, a mulher P95 é mais larga).
    folga_mm:
        Folga de projeto adicionada em cada extremo (mm).

    Returns
    -------
    dict
        ``{"medida", "minimo_mm", "maximo_mm", "curso_mm",
        "percentil_min", "percentil_max", "sexo"}``.

    Examples
    --------
    >>> faixa = calcular_faixa_ajuste("altura_poplitea")
    >>> faixa["curso_mm"] > 0
    True
    """
    if sexo == "ambos":
        # Envelope real: menor valor no percentil inferior e maior valor no
        # percentil superior, considerando ambos os sexos (o maior nem sempre
        # é o homem — ex.: largura do quadril).
        minimo = min(
            get_antropometria(medida, percentil_min, s) for s in sexos_disponiveis()
        )
        maximo = max(
            get_antropometria(medida, percentil_max, s) for s in sexos_disponiveis()
        )
    else:
        minimo = get_antropometria(medida, percentil_min, sexo)
        maximo = get_antropometria(medida, percentil_max, sexo)

    minimo -= folga_mm
    maximo += folga_mm

    return {
        "medida": medida,
        "descricao": MEDIDAS[medida]["descricao"],
        "minimo_mm": round(minimo, 1),
        "maximo_mm": round(maximo, 1),
        "curso_mm": round(maximo - minimo, 1),
        "percentil_min": percentil_min,
        "percentil_max": percentil_max,
        "sexo": sexo,
    }
