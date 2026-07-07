"""
Banco de dados de Padrão de Pegada (empunhadura / handle).
=========================================================

Modela a interface mão–máquina em três eixos independentes, que juntos
definem o "padrão de pegada" de um exercício:

1. **Orientação do punho** (:data:`ORIENTACOES_PUNHO`): pronada, supinada,
   neutra, mista/alternada.
2. **Largura da pegada** (:data:`LARGURAS_PEGADA`): relativa à largura
   biacromial (ombros) — fechada, média (dos ombros), aberta.
3. **Diâmetro da pega** (:data:`DIAMETRO_PEGA`): dimensionado a partir do
   comprimento da mão, conforme o objetivo (conforto/força máxima, força de
   preensão, precisão).

Diretrizes de diâmetro
----------------------
A literatura de ergonomia de preensão (power grip) aponta que o diâmetro
que maximiza conforto e força situa-se em torno de **~20% do comprimento
da mão** (tipicamente 30–45 mm para adultos). Pegas mais grossas
("fat grip", ~50–60 mm) deslocam a ênfase para a musculatura de preensão
do antebraço; pegas finas favorecem tarefas de precisão.

.. note::
   Diretrizes de projeto (seed). Ajuste com testes de usabilidade na
   população-alvo.
"""

from __future__ import annotations

from typing import TypedDict


class OrientacaoPunho(TypedDict):
    descricao: str
    angulo_antebraco_graus: float  # rotação do antebraço (0 = neutro)
    enfase: str


#: Orientações de punho e a ênfase muscular/articular típica.
ORIENTACOES_PUNHO: dict[str, OrientacaoPunho] = {
    "pronada": {
        "descricao": "Palmas para baixo/afastadas (overhand)",
        "angulo_antebraco_graus": 90,
        "enfase": "Dorsais/deltoide posterior e braquiorradial; punho estavel",
    },
    "supinada": {
        "descricao": "Palmas para cima/em direcao ao corpo (underhand)",
        "angulo_antebraco_graus": -90,
        "enfase": "Biceps braquial; maior ADM de flexao de cotovelo",
    },
    "neutra": {
        "descricao": "Palmas frente a frente (martelo/hammer)",
        "angulo_antebraco_graus": 0,
        "enfase": "Braquial/braquiorradial; menor estresse no punho e ombro",
    },
    "mista": {
        "descricao": "Uma mao pronada e outra supinada (alternada)",
        "angulo_antebraco_graus": 0,
        "enfase": "Maxima capacidade de carga (levantamento); assimetrica",
    },
}


class LarguraPegada(TypedDict):
    descricao: str
    fator_biacromial: float  # multiplicador da largura biacromial
    observacao: str


#: Larguras de pegada como múltiplo da largura biacromial (ombros).
LARGURAS_PEGADA: dict[str, LarguraPegada] = {
    "fechada": {
        "descricao": "Mais estreita que os ombros",
        "fator_biacromial": 0.75,
        "observacao": "Maior ADM; enfase em porcoes internas/triceps",
    },
    "media": {
        "descricao": "Aproximadamente na largura dos ombros",
        "fator_biacromial": 1.0,
        "observacao": "Pegada neutra/biomecanicamente equilibrada (padrao)",
    },
    "aberta": {
        "descricao": "Mais larga que os ombros",
        "fator_biacromial": 1.5,
        "observacao": "Enfase em porcoes externas; reduz ADM e sobrecarrega ombro",
    },
}


class ObjetivoPega(TypedDict):
    descricao: str
    fator_comprimento_mao: float  # diâmetro = fator × comprimento da mão
    faixa_mm: tuple[float, float]  # limites de sanidade (clamp)


#: Diâmetro da pega (cilíndrica) em função do objetivo de treino.
DIAMETRO_PEGA: dict[str, ObjetivoPega] = {
    "conforto": {
        "descricao": "Power grip otimo: maximo conforto e forca de trabalho",
        "fator_comprimento_mao": 0.20,
        "faixa_mm": (28.0, 45.0),
    },
    "forca_preensao": {
        "descricao": "Pega grossa (fat grip): enfase na preensao do antebraco",
        "fator_comprimento_mao": 0.30,
        "faixa_mm": (45.0, 60.0),
    },
    "precisao": {
        "descricao": "Pega fina: controle e tarefas de precisao",
        "fator_comprimento_mao": 0.14,
        "faixa_mm": (19.0, 28.0),
    },
}


def orientacoes_disponiveis() -> list[str]:
    return sorted(ORIENTACOES_PUNHO.keys())


def larguras_disponiveis() -> list[str]:
    return sorted(LARGURAS_PEGADA.keys())


def objetivos_pega_disponiveis() -> list[str]:
    return sorted(DIAMETRO_PEGA.keys())
