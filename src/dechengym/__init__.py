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
    parametros_geometria_de_ergonomia,
)
from dechengym.geracao_imagem import (
    gerar_preview_svg,
    gerar_imagem,
    renderizar_openscad_png,
    montar_prompt_imagem_produto,
)
from dechengym.sintese_came import (
    sintetizar_perfil_came,
    calcular_resistencia_came,
    gerar_came_openscad,
    gerar_came_svg,
    sintetizar_came_de_ergonomia,
)
from dechengym.orquestrador import (
    RequisicaoProjeto,
    projetar_maquina,
    orquestrar,
    adaptador_padrao,
)
from dechengym.montagem3d import (
    gerar_pecas_maquina,
    renderizar_svg_3d,
    gerar_visualizador_html,
)
from dechengym.ergonomia import (
    get_antropometria,
    calcular_faixa_ajuste,
    get_amplitude_movimento,
    validar_amplitude_projetada,
    get_padrao_pegada,
    dimensionar_pega,
    calcular_largura_pegada,
    get_curva_forca,
    gerar_perfil_resistencia_alvo,
    avaliar_curva_resistencia,
    calcular_alinhamento_pivo,
    projetar_ergonomia,
)

__version__ = "0.2.0"

__all__ = [
    # Cálculo estrutural
    "calc_momento_fletor",
    "get_especificacao_metalon",
    "validar_resistencia_estrutural",
    "recomendar_espessura_minima",
    # Geração de saída
    "gerar_script_openscad",
    "gerar_memorial_descritivo",
    "parametros_geometria_de_ergonomia",
    # Geração de imagem
    "gerar_preview_svg",
    "gerar_imagem",
    "renderizar_openscad_png",
    "montar_prompt_imagem_produto",
    # Síntese de came (resistência variável)
    "sintetizar_perfil_came",
    "calcular_resistencia_came",
    "gerar_came_openscad",
    "gerar_came_svg",
    "sintetizar_came_de_ergonomia",
    # Ergonomia
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
    # Orquestração
    "RequisicaoProjeto",
    "projetar_maquina",
    "orquestrar",
    "adaptador_padrao",
    # Montagem 3D
    "gerar_pecas_maquina",
    "renderizar_svg_3d",
    "gerar_visualizador_html",
]
