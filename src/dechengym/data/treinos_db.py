"""
Base de divisões de treino (splits) e grupos musculares.
========================================================

Liga o treino do usuário à Academia Virtual: cada letra de uma divisão
(ABC, ABCD, ABCDE) declara **grupos musculares**, e cada grupo mapeia para
os nomes de músculos usados em :mod:`dechengym.data.academia_db` — assim a
tela de treino mostra exatamente quais equipamentos da academia pertencem
a cada dia.

As **sinergias** registram o trabalho indireto (remar treina bíceps junto;
empurrar treina tríceps junto) e alimentam o motor de recuperação de
:mod:`dechengym.treino`.
"""

from __future__ import annotations

from typing import Any

#: Grupo muscular canônico -> nomes de músculos na academia_db.
GRUPOS_MUSCULARES: dict[str, list[str]] = {
    "peito": ["peitoral", "peitoral inferior"],
    "costas": ["dorsal", "romboides", "trapezio"],
    "ombros": ["deltoide", "deltoide anterior", "deltoide posterior"],
    "biceps": ["biceps", "braquial"],
    "triceps": ["triceps"],
    "pernas": ["quadriceps", "isquiotibiais", "gluteo", "gluteo medio",
               "adutores", "abdutores", "panturrilha"],
    "abdomen": ["reto abdominal", "obliquos", "core"],
    "lombar": ["lombar"],
}

#: Trabalho indireto: treinar o grupo-chave também carrega os sinergistas.
SINERGIAS: dict[str, list[str]] = {
    "costas": ["biceps"],
    "peito": ["triceps", "ombros"],
    "ombros": ["triceps"],
    "pernas": ["lombar"],
}

#: Descanso mínimo recomendado (horas -> dias) por grupo antes de repetir.
DESCANSO_MINIMO_DIAS: int = 2

#: Divisões de treino disponíveis. A ordem das letras é a ordem sugerida
#: do ciclo; o motor de sugestão reordena pelo estado de recuperação.
DIVISOES: dict[str, dict[str, Any]] = {
    "abc": {
        "nome": "ABC (3 treinos por ciclo)",
        "letras": {
            "A": {"nome": "Empurrar — Peito, Ombros e Tríceps",
                  "grupos": ["peito", "ombros", "triceps"]},
            "B": {"nome": "Puxar — Costas e Bíceps",
                  "grupos": ["costas", "biceps"]},
            "C": {"nome": "Pernas completas",
                  "grupos": ["pernas"]},
        },
    },
    "abcd": {
        "nome": "ABCD (4 treinos por ciclo)",
        "letras": {
            "A": {"nome": "Peito e Tríceps", "grupos": ["peito", "triceps"]},
            "B": {"nome": "Costas e Bíceps", "grupos": ["costas", "biceps"]},
            "C": {"nome": "Ombros e Abdômen", "grupos": ["ombros", "abdomen"]},
            "D": {"nome": "Pernas completas", "grupos": ["pernas"]},
        },
    },
    "abcde": {
        "nome": "ABCDE (5 treinos por ciclo)",
        "letras": {
            "A": {"nome": "Peito", "grupos": ["peito"]},
            "B": {"nome": "Costas", "grupos": ["costas"]},
            "C": {"nome": "Pernas", "grupos": ["pernas"]},
            "D": {"nome": "Ombros e Abdômen", "grupos": ["ombros", "abdomen"]},
            "E": {"nome": "Braços — Bíceps e Tríceps",
                  "grupos": ["biceps", "triceps"]},
        },
    },
}

DIVISAO_PADRAO = "abcde"


def musculos_do_grupo(grupo: str) -> list[str]:
    """Nomes de músculos (academia_db) de um grupo canônico."""
    return GRUPOS_MUSCULARES.get(grupo, [])


def grupos_indiretos(grupo: str) -> list[str]:
    """Sinergistas carregados indiretamente ao treinar ``grupo``."""
    return SINERGIAS.get(grupo, [])


def equipamentos_do_treino(grupos: list[str]) -> list[dict[str, Any]]:
    """Equipamentos da Academia Virtual que atendem os grupos do treino."""
    from dechengym.data.academia_db import ACADEMIA_VIRTUAL

    alvo = {m for g in grupos for m in musculos_do_grupo(g)}
    achados = []
    for chave, e in ACADEMIA_VIRTUAL.items():
        if alvo.intersection(e["musculos"]):
            achados.append({
                "id": chave,
                "nome": e["nome"],
                "musculos": e["musculos"],
                "rank": e["rank"],
                "projeto_completo": e["exercicio_pipeline"] is not None,
                "exercicio_pipeline": e["exercicio_pipeline"],
            })
    achados.sort(key=lambda x: x["rank"])
    return achados
