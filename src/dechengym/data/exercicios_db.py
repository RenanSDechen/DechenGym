"""
Catálogo de exercícios de máquinas articuladas.
==============================================

Cada exercício associa o padrão de movimento a: articulação e movimento
principais (para ADM e alinhamento do pivô), grupo muscular (para a curva
de força), pegada padrão (orientação/largura) e a medida antropométrica de
referência para o alinhamento do eixo da máquina com o eixo articular.

Serve de entrada para o integrador :func:`dechengym.ergonomia.projeto.projetar_ergonomia`.
"""

from __future__ import annotations

from typing import TypedDict


class Exercicio(TypedDict):
    nome: str
    articulacao: str
    movimento: str
    grupo_muscular: str
    pegada_orientacao: str
    pegada_largura: str
    # Medida antropométrica que define a altura/posição do eixo de pivô.
    medida_alinhamento_pivo: str
    postura: str  # "sentado" | "em_pe" | "deitado"


CATALOGO_EXERCICIOS: dict[str, Exercicio] = {
    "rosca_biceps": {
        "nome": "Rosca de biceps (maquina)",
        "articulacao": "cotovelo",
        "movimento": "flexao",
        "grupo_muscular": "biceps",
        "pegada_orientacao": "supinada",
        "pegada_largura": "media",
        "medida_alinhamento_pivo": "altura_cotovelo_sentado",
        "postura": "sentado",
    },
    "triceps_maquina": {
        "nome": "Extensao de triceps (maquina)",
        "articulacao": "cotovelo",
        "movimento": "extensao",
        "grupo_muscular": "triceps",
        "pegada_orientacao": "neutra",
        "pegada_largura": "media",
        "medida_alinhamento_pivo": "altura_cotovelo_sentado",
        "postura": "sentado",
    },
    "supino_maquina": {
        "nome": "Supino/pressao de peito (maquina)",
        "articulacao": "ombro",
        "movimento": "aducao_horizontal",
        "grupo_muscular": "peitoral",
        "pegada_orientacao": "pronada",
        "pegada_largura": "media",
        "medida_alinhamento_pivo": "altura_ombro_sentado",
        "postura": "sentado",
    },
    "remada_maquina": {
        "nome": "Remada sentada (maquina)",
        "articulacao": "ombro",
        "movimento": "extensao",
        "grupo_muscular": "dorsal",
        "pegada_orientacao": "neutra",
        "pegada_largura": "media",
        "medida_alinhamento_pivo": "altura_ombro_sentado",
        "postura": "sentado",
    },
    "desenvolvimento_maquina": {
        "nome": "Desenvolvimento de ombros (maquina)",
        "articulacao": "ombro",
        "movimento": "abducao",
        "grupo_muscular": "deltoide",
        "pegada_orientacao": "pronada",
        "pegada_largura": "aberta",
        "medida_alinhamento_pivo": "altura_ombro_sentado",
        "postura": "sentado",
    },
    "cadeira_extensora": {
        "nome": "Cadeira extensora",
        "articulacao": "joelho",
        "movimento": "extensao",
        "grupo_muscular": "quadriceps",
        "pegada_orientacao": "neutra",
        "pegada_largura": "media",
        "medida_alinhamento_pivo": "altura_poplitea",
        "postura": "sentado",
    },
    "mesa_flexora": {
        "nome": "Mesa/cadeira flexora",
        "articulacao": "joelho",
        "movimento": "flexao",
        "grupo_muscular": "isquiotibiais",
        "pegada_orientacao": "neutra",
        "pegada_largura": "media",
        "medida_alinhamento_pivo": "altura_poplitea",
        "postura": "sentado",
    },
    "cadeira_abdutora": {
        "nome": "Cadeira abdutora",
        "articulacao": "quadril",
        "movimento": "abducao",
        "grupo_muscular": "gluteo",
        "pegada_orientacao": "neutra",
        "pegada_largura": "media",
        "medida_alinhamento_pivo": "altura_ombro_sentado",
        "postura": "sentado",
    },
}


def exercicios_disponiveis() -> list[str]:
    return sorted(CATALOGO_EXERCICIOS.keys())
