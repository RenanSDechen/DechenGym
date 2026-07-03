"""
DechenGym
=========

Núcleo de IA para projeto de equipamentos de musculação (máquinas
articuladas) com foco em ergonomia, cálculo estrutural e geração de
código paramétrico (OpenSCAD) + memorial descritivo.

A arquitetura é orientada a *Tool Calling*: cada capacidade de engenharia
é exposta como uma função Python pura e determinística que um LLM
orquestrador (Langflow, SDK, etc.) pode invocar.

Módulos principais
------------------
- :mod:`dechengym.calculo_estrutural` : momento fletor, especificação de
  metalon e validação de resistência.
- :mod:`dechengym.geracao_openscad`   : geração do script OpenSCAD e do
  memorial descritivo (JSON).
- :mod:`dechengym.tools`              : registro/schemas das Tools para o
  orquestrador de agentes.
"""

from dechengym.calculo_estrutural import (
    calc_momento_fletor,
    get_especificacao_metalon,
    validar_resistencia_estrutural,
    recomendar_espessura_minima,
)
from dechengym.geracao_openscad import (
    gerar_script_openscad,
    gerar_memorial_descritivo,
)

__version__ = "0.1.0"

__all__ = [
    "calc_momento_fletor",
    "get_especificacao_metalon",
    "validar_resistencia_estrutural",
    "recomendar_espessura_minima",
    "gerar_script_openscad",
    "gerar_memorial_descritivo",
]
