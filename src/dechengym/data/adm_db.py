"""
Banco de dados de Amplitude de Movimento articular (ADM / ROM).
==============================================================

Para cada articulação e movimento, guardamos:

- ``adm_anatomica``: faixa anatômica normal (graus), referenciada à posição
  neutra (0°).
- ``adm_treino``: faixa **recomendada para projeto de máquina** — um pouco
  mais conservadora que a anatômica, evitando os extremos de amplitude
  (onde há maior risco articular e menor produção de força).

Projetar o curso do braço articulado dentro de ``adm_treino`` é o critério
ergonômico central: a máquina não deve forçar a articulação além do que é
seguro e produtivo.

.. note::
   Valores representativos de ADM ativa de adultos saudáveis (compatíveis
   com AAOS / Kapandji). Ajuste conforme a população e o objetivo do
   equipamento.
"""

from __future__ import annotations

from typing import TypedDict


class Movimento(TypedDict):
    adm_anatomica: tuple[float, float]
    adm_treino: tuple[float, float]
    descricao: str


#: ADM[articulacao][movimento] -> faixas em graus.
ADM: dict[str, dict[str, Movimento]] = {
    "ombro": {
        "flexao": {
            "adm_anatomica": (0, 180),
            "adm_treino": (0, 160),
            "descricao": "Elevar o braco a frente",
        },
        "extensao": {
            "adm_anatomica": (0, 60),
            "adm_treino": (0, 45),
            "descricao": "Levar o braco para tras",
        },
        "abducao": {
            "adm_anatomica": (0, 180),
            "adm_treino": (0, 160),
            "descricao": "Afastar o braco lateralmente",
        },
        "aducao_horizontal": {
            "adm_anatomica": (0, 135),
            "adm_treino": (0, 120),
            "descricao": "Cruzar o braco a frente (ex.: crucifixo/supino)",
        },
        "rotacao_interna": {
            "adm_anatomica": (0, 90),
            "adm_treino": (0, 70),
            "descricao": "Girar o braco para dentro",
        },
        "rotacao_externa": {
            "adm_anatomica": (0, 90),
            "adm_treino": (0, 80),
            "descricao": "Girar o braco para fora",
        },
    },
    "cotovelo": {
        "flexao": {
            "adm_anatomica": (0, 145),
            "adm_treino": (10, 135),
            "descricao": "Dobrar o cotovelo (ex.: rosca)",
        },
        "extensao": {
            "adm_anatomica": (0, 0),
            "adm_treino": (0, 0),
            "descricao": "Estender o cotovelo (retorno da flexao)",
        },
        "pronacao": {
            "adm_anatomica": (0, 85),
            "adm_treino": (0, 75),
            "descricao": "Girar o antebraco (palma p/ baixo)",
        },
        "supinacao": {
            "adm_anatomica": (0, 85),
            "adm_treino": (0, 75),
            "descricao": "Girar o antebraco (palma p/ cima)",
        },
    },
    "quadril": {
        "flexao": {
            "adm_anatomica": (0, 120),
            "adm_treino": (0, 100),
            "descricao": "Levar a coxa a frente",
        },
        "extensao": {
            "adm_anatomica": (0, 30),
            "adm_treino": (0, 20),
            "descricao": "Levar a coxa para tras",
        },
        "abducao": {
            "adm_anatomica": (0, 45),
            "adm_treino": (0, 40),
            "descricao": "Afastar a coxa (ex.: cadeira abdutora)",
        },
        "aducao": {
            "adm_anatomica": (0, 30),
            "adm_treino": (0, 25),
            "descricao": "Aproximar a coxa (ex.: cadeira adutora)",
        },
    },
    "joelho": {
        "flexao": {
            "adm_anatomica": (0, 135),
            "adm_treino": (0, 120),
            "descricao": "Dobrar o joelho (ex.: mesa flexora)",
        },
        "extensao": {
            "adm_anatomica": (0, 0),
            "adm_treino": (0, 0),
            "descricao": "Estender o joelho (ex.: cadeira extensora)",
        },
    },
    "tornozelo": {
        "dorsiflexao": {
            "adm_anatomica": (0, 20),
            "adm_treino": (0, 15),
            "descricao": "Puxar o pe para cima",
        },
        "plantiflexao": {
            "adm_anatomica": (0, 50),
            "adm_treino": (0, 40),
            "descricao": "Empurrar o pe para baixo (ex.: panturrilha)",
        },
    },
}


def articulacoes_disponiveis() -> list[str]:
    return sorted(ADM.keys())
