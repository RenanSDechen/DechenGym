"""
Pacote de Ergonomia
===================

Ferramentas (Tools) determinísticas de ergonomia e biomecânica para o
projeto de máquinas articuladas. Cada função é pura e pensada para ser
invocada via Tool Calling pelo LLM orquestrador.

Submódulos
----------
- :mod:`~dechengym.ergonomia.antropometria` : dimensões corporais e faixas
  de ajuste (envelope P5–P95).
- :mod:`~dechengym.ergonomia.amplitude`     : amplitude de movimento (ADM)
  e validação do curso projetado.
- :mod:`~dechengym.ergonomia.pegada`        : padrão de pegada (orientação,
  largura e diâmetro da pega).
- :mod:`~dechengym.ergonomia.curva_resistencia` : curva de força humana e
  avaliação do casamento com a resistência da máquina.
- :mod:`~dechengym.ergonomia.projeto`       : integrador que consolida um
  envelope ergonômico completo para um exercício.
"""

from dechengym.ergonomia.amplitude import (
    get_amplitude_movimento,
    validar_amplitude_projetada,
)
from dechengym.ergonomia.antropometria import (
    calcular_faixa_ajuste,
    get_antropometria,
)
from dechengym.ergonomia.curva_resistencia import (
    avaliar_curva_resistencia,
    gerar_perfil_resistencia_alvo,
    get_curva_forca,
)
from dechengym.ergonomia.pegada import (
    calcular_largura_pegada,
    dimensionar_pega,
    get_padrao_pegada,
)
from dechengym.ergonomia.projeto import (
    calcular_alinhamento_pivo,
    projetar_ergonomia,
)

__all__ = [
    "get_antropometria",
    "calcular_faixa_ajuste",
    "get_amplitude_movimento",
    "validar_amplitude_projetada",
    "get_padrao_pegada",
    "dimensionar_pega",
    "calcular_largura_pegada",
    "get_curva_forca",
    "gerar_perfil_resistencia_alvo",
    "avaliar_curva_resistencia",
    "calcular_alinhamento_pivo",
    "projetar_ergonomia",
]
