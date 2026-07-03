"""
Banco de dados antropométrico (mockado/seed).
=============================================

Dimensões corporais de adultos por **sexo** e **percentil** (P5, P50, P95),
em **milímetros**. São a base para dimensionar faixas de ajuste (curso de
regulagem) de bancos, encostos, braços de alavanca e pegas, de modo a
acomodar da mulher P5 ao homem P95 — o "envelope antropométrico" clássico
de projeto (5º ao 95º percentil).

.. important::
   Os valores são **representativos** (ordem de grandeza compatível com
   tabelas publicadas — ISO 7250 / Panero & Zelnik / DINED). Para projeto
   final, substitua por uma fonte validada da população-alvo.

Referência postural: a maioria das medidas "sentado" é tomada a partir do
**plano do assento** (SRP — Seat Reference Point), exceto as medidas de
alcance e as globais (estatura).
"""

from __future__ import annotations

from typing import TypedDict


class MetaMedida(TypedDict):
    descricao: str
    unidade: str
    referencia: str


#: Metadados (semântica) de cada medida antropométrica.
MEDIDAS: dict[str, MetaMedida] = {
    "estatura": {
        "descricao": "Altura total em pe",
        "unidade": "mm",
        "referencia": "piso",
    },
    "altura_sentado": {
        "descricao": "Altura do topo da cabeca ao assento (tronco ereto)",
        "unidade": "mm",
        "referencia": "assento",
    },
    "altura_poplitea": {
        "descricao": "Altura da dobra do joelho ao piso (define altura do assento)",
        "unidade": "mm",
        "referencia": "piso",
    },
    "comprimento_nadega_poplitea": {
        "descricao": "Profundidade do assento util (nadega a dobra do joelho)",
        "unidade": "mm",
        "referencia": "encosto",
    },
    "altura_ombro_sentado": {
        "descricao": "Altura do acromio (ombro) acima do assento",
        "unidade": "mm",
        "referencia": "assento",
    },
    "altura_cotovelo_sentado": {
        "descricao": "Altura do cotovelo em repouso acima do assento",
        "unidade": "mm",
        "referencia": "assento",
    },
    "largura_biacromial": {
        "descricao": "Largura entre os ombros (acromios) - base p/ largura de pegada",
        "unidade": "mm",
        "referencia": "-",
    },
    "largura_quadril_sentado": {
        "descricao": "Largura do quadril sentado - base p/ largura do assento",
        "unidade": "mm",
        "referencia": "-",
    },
    "comprimento_antebraco_mao": {
        "descricao": "Cotovelo a ponta dos dedos (alcance de flexao de cotovelo)",
        "unidade": "mm",
        "referencia": "cotovelo",
    },
    "comprimento_bracco_superior": {
        "descricao": "Acromio ao cotovelo (comprimento do braco)",
        "unidade": "mm",
        "referencia": "acromio",
    },
    "comprimento_mao": {
        "descricao": "Punho a ponta do dedo medio (base p/ diametro da pega)",
        "unidade": "mm",
        "referencia": "punho",
    },
    "largura_mao": {
        "descricao": "Largura da mao na regiao dos metacarpos",
        "unidade": "mm",
        "referencia": "-",
    },
    "altura_joelho_sentado": {
        "descricao": "Altura do topo do joelho acima do piso (folga sob apoios)",
        "unidade": "mm",
        "referencia": "piso",
    },
    "espessura_coxa": {
        "descricao": "Espessura da coxa sentado (folga sob apoios/pegas)",
        "unidade": "mm",
        "referencia": "assento",
    },
    "alcance_frontal_pega": {
        "descricao": "Alcance frontal ate o centro da mao em preensao",
        "unidade": "mm",
        "referencia": "ombro",
    },
}


# Percentis anchor disponíveis. Valores intermediários são interpolados.
PERCENTIS_ANCORA: tuple[int, ...] = (5, 50, 95)


#: DADOS[sexo][medida][percentil] -> valor em mm.
DADOS: dict[str, dict[str, dict[int, float]]] = {
    "masculino": {
        "estatura": {5: 1650, 50: 1755, 95: 1870},
        "altura_sentado": {5: 855, 50: 915, 95: 970},
        "altura_poplitea": {5: 395, 50: 440, 95: 490},
        "comprimento_nadega_poplitea": {5: 450, 50: 495, 95: 550},
        "altura_ombro_sentado": {5: 545, 50: 600, 95: 645},
        "altura_cotovelo_sentado": {5: 195, 50: 245, 95: 295},
        "largura_biacromial": {5: 370, 50: 400, 95: 430},
        "largura_quadril_sentado": {5: 310, 50: 350, 95: 400},
        "comprimento_antebraco_mao": {5: 440, 50: 475, 95: 510},
        "comprimento_bracco_superior": {5: 330, 50: 360, 95: 390},
        "comprimento_mao": {5: 175, 50: 189, 95: 205},
        "largura_mao": {5: 80, 50: 87, 95: 95},
        "altura_joelho_sentado": {5: 490, 50: 545, 95: 600},
        "espessura_coxa": {5: 135, 50: 160, 95: 185},
        "alcance_frontal_pega": {5: 720, 50: 780, 95: 840},
    },
    "feminino": {
        "estatura": {5: 1520, 50: 1625, 95: 1730},
        "altura_sentado": {5: 795, 50: 850, 95: 910},
        "altura_poplitea": {5: 355, 50: 400, 95: 445},
        "comprimento_nadega_poplitea": {5: 435, 50: 480, 95: 530},
        "altura_ombro_sentado": {5: 505, 50: 555, 95: 610},
        "altura_cotovelo_sentado": {5: 185, 50: 235, 95: 280},
        "largura_biacromial": {5: 330, 50: 355, 95: 385},
        "largura_quadril_sentado": {5: 315, 50: 360, 95: 420},
        "comprimento_antebraco_mao": {5: 400, 50: 430, 95: 465},
        "comprimento_bracco_superior": {5: 300, 50: 330, 95: 360},
        "comprimento_mao": {5: 160, 50: 174, 95: 190},
        "largura_mao": {5: 70, 50: 76, 95: 84},
        "altura_joelho_sentado": {5: 455, 50: 500, 95: 550},
        "espessura_coxa": {5: 125, 50: 155, 95: 180},
        "alcance_frontal_pega": {5: 650, 50: 705, 95: 765},
    },
}


def sexos_disponiveis() -> list[str]:
    return sorted(DADOS.keys())


def medidas_disponiveis() -> list[str]:
    return sorted(MEDIDAS.keys())
