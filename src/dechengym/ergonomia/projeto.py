"""
Integrador de projeto ergonômico.
=================================

Consolida as ferramentas de ergonomia em um único "envelope ergonômico"
para um exercício do catálogo: faixas de ajuste (assento, encosto),
alinhamento do eixo de pivô com o eixo articular, amplitude de movimento
recomendada, padrão de pegada completo e curva de força alvo.

O resultado alimenta diretamente o módulo de Geração OpenSCAD (dimensões e
eixos) e o memorial descritivo.
"""

from __future__ import annotations

from typing import Any

from dechengym.data.exercicios_db import (
    CATALOGO_EXERCICIOS,
    exercicios_disponiveis,
)
from dechengym.ergonomia.amplitude import get_amplitude_movimento
from dechengym.ergonomia.antropometria import calcular_faixa_ajuste, get_antropometria
from dechengym.ergonomia.curva_resistencia import gerar_perfil_resistencia_alvo
from dechengym.ergonomia.pegada import (
    calcular_largura_pegada,
    dimensionar_pega,
    get_padrao_pegada,
)


def calcular_alinhamento_pivo(
    medida_alinhamento: str,
    percentil: float = 50,
    sexo: str = "masculino",
) -> dict[str, Any]:
    """Calcula a altura do eixo de pivô para alinhar com o eixo articular.

    O princípio ergonômico fundamental de uma máquina articulada é que seu
    eixo mecânico coincida com o eixo anatômico de rotação da articulação
    trabalhada. A altura de referência vem da medida antropométrica do
    exercício (ex.: altura do cotovelo sentado para uma rosca).

    Também retorna a faixa P5–P95 para o componente que ajusta esse
    alinhamento (assento/encosto).
    """
    altura = get_antropometria(medida_alinhamento, percentil, sexo)
    faixa = calcular_faixa_ajuste(medida_alinhamento)
    return {
        "medida_referencia": medida_alinhamento,
        "altura_pivo_mm": round(altura, 1),
        "percentil": percentil,
        "sexo": sexo,
        "faixa_ajuste_p5_p95": faixa,
    }


def projetar_ergonomia(
    exercicio: str,
    percentil: float = 50,
    sexo: str = "masculino",
    carga_pico_kg: float = 100,
    objetivo_pega: str = "conforto",
) -> dict[str, Any]:
    """Gera o envelope ergonômico completo de um exercício.

    Orquestra todas as ferramentas de ergonomia para produzir uma
    especificação consolidada, pronta para alimentar a geração de geometria.

    Parameters
    ----------
    exercicio:
        Chave do catálogo (ver
        :data:`dechengym.data.exercicios_db.CATALOGO_EXERCICIOS`),
        ex.: ``"rosca_biceps"``, ``"cadeira_extensora"``.
    percentil, sexo:
        Usuário de referência para o dimensionamento nominal.
    carga_pico_kg:
        Carga de pico para gerar a curva de resistência-alvo.
    objetivo_pega:
        Objetivo da pega (``"conforto"``/``"forca_preensao"``/``"precisao"``).

    Returns
    -------
    dict
        Envelope ergonômico consolidado.

    Raises
    ------
    KeyError
        Se o exercício não existir no catálogo.
    """
    if exercicio not in CATALOGO_EXERCICIOS:
        raise KeyError(
            f"Exercicio '{exercicio}' invalido. Use: {exercicios_disponiveis()}"
        )

    ex = CATALOGO_EXERCICIOS[exercicio]

    # 1) Alinhamento do eixo de pivô + faixa de ajuste do componente.
    alinhamento = calcular_alinhamento_pivo(
        ex["medida_alinhamento_pivo"], percentil, sexo
    )

    # 2) Amplitude de movimento recomendada.
    adm = get_amplitude_movimento(ex["articulacao"], ex["movimento"])

    # 3) Padrão de pegada completo (orientação + largura + diâmetro).
    orientacao = get_padrao_pegada(ex["pegada_orientacao"])
    largura = calcular_largura_pegada(ex["pegada_largura"], percentil, sexo)
    diametro = dimensionar_pega(objetivo_pega, percentil, sexo)

    # 4) Faixas de ajuste ergonômico do posto (assento e profundidade).
    ajuste_assento = calcular_faixa_ajuste("altura_poplitea")
    ajuste_profundidade = calcular_faixa_ajuste("comprimento_nadega_poplitea")

    # 5) Curva de resistência-alvo (casa com a curva de força humana).
    resistencia_alvo = gerar_perfil_resistencia_alvo(
        ex["grupo_muscular"], carga_pico_kg
    )

    return {
        "exercicio": exercicio,
        "nome": ex["nome"],
        "usuario_referencia": {"percentil": percentil, "sexo": sexo},
        "articulacao": ex["articulacao"],
        "movimento": ex["movimento"],
        "grupo_muscular": ex["grupo_muscular"],
        "alinhamento_pivo": alinhamento,
        "amplitude_movimento": adm,
        "pegada": {
            "orientacao": orientacao,
            "largura": largura,
            "diametro": diametro,
        },
        "ajustes_posto": {
            "altura_assento": ajuste_assento,
            "profundidade_assento": ajuste_profundidade,
        },
        "curva_resistencia_alvo": resistencia_alvo,
    }
