"""
Banco de dados de Curvas de Força humanas (strength curves).
===========================================================

A força que uma articulação consegue produzir **varia ao longo da amplitude
de movimento**. Uma máquina bem projetada faz a resistência acompanhar essa
curva (via geometria do braço/came), mantendo a solicitação muscular
adequada do início ao fim do movimento.

Tipos clássicos de curva de força:

- **ascendente**: força cresce ao longo do movimento (ex.: supino,
  desenvolvimento, extensão de joelho — mais forte perto da extensão).
- **descendente**: força é maior no início (ex.: remada, puxada).
- **sino** (bell): pico no meio da amplitude (ex.: rosca de bíceps, mais
  forte por volta de 90° de flexão de cotovelo).

O perfil é amostrado em 5 pontos ao longo do movimento (0%, 25%, 50%, 75%,
100%), com o fator de força relativo normalizado (0–1, sendo 1 o pico).

.. note::
   Perfis representativos (seed). Refine com dinamometria isocinética da
   população-alvo para cada exercício.
"""

from __future__ import annotations

from typing import TypedDict


class CurvaForca(TypedDict):
    tipo: str
    # Fator de força relativo (0-1) em 0%, 25%, 50%, 75%, 100% do movimento.
    perfil: tuple[float, float, float, float, float]
    descricao: str


#: Pontos percentuais em que o perfil é amostrado.
AMOSTRAS_PCT: tuple[int, ...] = (0, 25, 50, 75, 100)


#: Curva de força por grupo muscular / padrão de movimento.
CURVAS_FORCA: dict[str, CurvaForca] = {
    "biceps": {
        "tipo": "sino",
        "perfil": (0.55, 0.85, 1.00, 0.85, 0.55),
        "descricao": "Flexao de cotovelo: pico proximo a 90 graus",
    },
    "triceps": {
        "tipo": "ascendente",
        "perfil": (0.60, 0.72, 0.82, 0.92, 1.00),
        "descricao": "Extensao de cotovelo: mais forte perto da extensao",
    },
    "peitoral": {
        "tipo": "ascendente",
        "perfil": (0.65, 0.78, 0.88, 0.96, 1.00),
        "descricao": "Supino/pressao: mais forte perto da extensao (lockout)",
    },
    "dorsal": {
        "tipo": "descendente",
        "perfil": (1.00, 0.92, 0.82, 0.72, 0.62),
        "descricao": "Remada/puxada: mais forte no inicio da tracao",
    },
    "deltoide": {
        "tipo": "ascendente",
        "perfil": (0.62, 0.75, 0.86, 0.95, 1.00),
        "descricao": "Desenvolvimento: mais forte perto da extensao",
    },
    "quadriceps": {
        # O torque extensor do joelho tem pico proximo a 60 graus de flexao e
        # cai na extensao terminal (onde ha maior estresse patelofemoral); nao
        # e "ascendente ate a extensao total".
        "tipo": "sino",
        "perfil": (0.75, 1.00, 0.90, 0.74, 0.58),
        "descricao": "Extensao de joelho: pico ~60 graus de flexao, fraco na extensao final",
    },
    "isquiotibiais": {
        "tipo": "descendente",
        "perfil": (1.00, 0.90, 0.80, 0.70, 0.60),
        "descricao": "Flexao de joelho: mais forte no inicio da flexao",
    },
    "gluteo": {
        "tipo": "sino",
        "perfil": (0.60, 0.85, 1.00, 0.88, 0.62),
        "descricao": "Extensao de quadril: pico na regiao media",
    },
    "abdutores_quadril": {
        # Abducao de quadril (gluteo medio/minimo): mais forte proximo do
        # neutro/aducao e enfraquece conforme a abducao avanca.
        "tipo": "descendente",
        "perfil": (1.00, 0.90, 0.80, 0.70, 0.60),
        "descricao": "Abducao de quadril: mais forte no inicio (proximo ao neutro)",
    },
    "panturrilha": {
        "tipo": "descendente",
        "perfil": (1.00, 0.88, 0.76, 0.66, 0.58),
        "descricao": "Flexao plantar: mais forte no alongamento inicial",
    },
}


def grupos_disponiveis() -> list[str]:
    return sorted(CURVAS_FORCA.keys())
