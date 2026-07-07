"""
Banco de dados mockado de perfis de aço (metalon).

Em vez de gravar uma tabela gigante de propriedades já calculadas, guardamos
apenas os dados de catálogo (dimensões externas, espessuras disponíveis e
propriedades do material). As propriedades de seção (área, momento de
inércia, módulo de seção, peso por metro) são calculadas sob demanda em
:mod:`dechengym.calculo_estrutural`, o que mantém o banco enxauto e evita
divergência entre valores tabelados.

Perfis "metalon" são tubos de aço de seção quadrada ou retangular, muito
usados no Brasil para estruturas de máquinas. As chaves seguem a notação
comercial ``"BASExALTURA"`` em milímetros (ex.: ``"50x50"``, ``"60x40"``).
"""

from __future__ import annotations

from typing import TypedDict


class PerfilMetalon(TypedDict):
    """Registro de catálogo de um perfil de metalon."""

    base_mm: float
    altura_mm: float
    espessuras_mm: tuple[float, ...]
    material: str
    limite_escoamento_mpa: float


# Limite de escoamento típico do aço carbono estrutural comumente usado em
# metalon comercial (equivalente a ASTM A36 / SAE 1010-1020). Unidade: MPa.
_ESCOAMENTO_ACO_COMUM_MPA: float = 250.0
_MATERIAL_PADRAO: str = "Aco carbono (ASTM A36 / SAE 1010-1020)"

# Espessuras de parede tipicamente disponíveis em distribuidoras.
_ESPESSURAS_PADRAO: tuple[float, ...] = (0.9, 1.2, 1.5, 2.0, 3.0)


def _perfil(base_mm: float, altura_mm: float, *, espessuras=_ESPESSURAS_PADRAO) -> PerfilMetalon:
    """Helper para montar um registro de perfil com o material padrão."""
    return PerfilMetalon(
        base_mm=base_mm,
        altura_mm=altura_mm,
        espessuras_mm=espessuras,
        material=_MATERIAL_PADRAO,
        limite_escoamento_mpa=_ESCOAMENTO_ACO_COMUM_MPA,
    )


#: Catálogo mockado de perfis de metalon indexado pela notação comercial.
CATALOGO_METALON: dict[str, PerfilMetalon] = {
    # Quadrados
    "20x20": _perfil(20, 20),
    "30x30": _perfil(30, 30),
    "40x40": _perfil(40, 40),
    "50x50": _perfil(50, 50),
    "60x60": _perfil(60, 60, espessuras=(1.2, 1.5, 2.0, 3.0, 4.75)),
    # Retangulares
    "40x20": _perfil(40, 20),
    "50x30": _perfil(50, 30),
    "60x40": _perfil(60, 40, espessuras=(1.2, 1.5, 2.0, 3.0, 4.75)),
    "80x40": _perfil(80, 40, espessuras=(1.5, 2.0, 3.0, 4.75)),
    # Perfis industriais de máquinas de musculação (memoriais descritivos de
    # mercado): 75x35 e 80x40 com parede 2,0-3,0 mm. As entradas com a
    # ALTURA maior ("35x75", "40x80") representam o perfil orientado com a
    # alma na vertical — a orientação correta para flexão da alavanca.
    "75x35": _perfil(75, 35, espessuras=(2.0, 3.0)),
    "35x75": _perfil(35, 75, espessuras=(2.0, 3.0)),
    "40x80": _perfil(40, 80, espessuras=(1.5, 2.0, 3.0, 4.75)),
}


def perfis_disponiveis() -> list[str]:
    """Retorna a lista de perfis existentes no catálogo."""
    return sorted(CATALOGO_METALON.keys())
