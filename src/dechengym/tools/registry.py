"""
Registro de Tools para orquestração de agentes (Tool Calling).
=============================================================

Este módulo é a "cola" entre as funções puras de engenharia e o LLM
orquestrador. Ele expõe:

- :data:`TOOLS`        — mapa ``nome -> função Python``.
- :data:`TOOL_SCHEMAS` — schemas no formato "tool use" (compatível com a
  API de tools da Anthropic / OpenAI), consumível também por Langflow.
- :func:`executar_tool` — despacha uma chamada de tool pelo nome.

Mantemos os schemas escritos à mão (e não gerados por reflexão) para que o
contrato apresentado ao LLM seja explícito, revisável e estável.
"""

from __future__ import annotations

from typing import Any, Callable

from dechengym.calculo_estrutural import (
    calc_momento_fletor,
    get_especificacao_metalon,
    recomendar_espessura_minima,
    validar_resistencia_estrutural,
)
from dechengym.geracao_openscad import (
    gerar_memorial_descritivo,
    gerar_script_openscad,
)
from dechengym.geracao_imagem import (
    gerar_preview_svg,
    montar_prompt_imagem_produto,
    renderizar_openscad_png,
)
from dechengym.sintese_came import (
    calcular_resistencia_came,
    gerar_came_openscad,
    gerar_came_svg,
    sintetizar_came_de_ergonomia,
    sintetizar_perfil_came,
)
from dechengym.orquestrador.pipeline import projetar_maquina_params
from dechengym.academia import gerar_catalogo_academia, gerar_planta_academia
from dechengym.data.padroes_db import (
    get_padrao_biblioteca,
    listar_biblioteca_padroes,
)
from dechengym.data.projetos_referencia_db import (
    get_projeto_referencia,
    listar_padroes_construtivos,
)
from dechengym.montagem3d import (
    gerar_pecas_maquina,
    gerar_visualizador_html,
    renderizar_svg_3d,
)
from dechengym.ergonomia import (
    avaliar_curva_resistencia,
    calcular_alinhamento_pivo,
    calcular_faixa_ajuste,
    calcular_largura_pegada,
    dimensionar_pega,
    gerar_perfil_resistencia_alvo,
    get_amplitude_movimento,
    get_antropometria,
    get_curva_forca,
    get_padrao_pegada,
    projetar_ergonomia,
    validar_amplitude_projetada,
)

#: Mapa nome -> callable. É a fonte de verdade da execução.
TOOLS: dict[str, Callable[..., Any]] = {
    # --- Cálculo estrutural ---
    "calc_momento_fletor": calc_momento_fletor,
    "get_especificacao_metalon": get_especificacao_metalon,
    "validar_resistencia_estrutural": validar_resistencia_estrutural,
    "recomendar_espessura_minima": recomendar_espessura_minima,
    # --- Geração de saída ---
    "gerar_script_openscad": gerar_script_openscad,
    "gerar_memorial_descritivo": gerar_memorial_descritivo,
    # --- Geração de imagem ---
    "gerar_preview_svg": gerar_preview_svg,
    "renderizar_openscad_png": renderizar_openscad_png,
    "montar_prompt_imagem_produto": montar_prompt_imagem_produto,
    # --- Síntese de came (resistência variável) ---
    "sintetizar_perfil_came": sintetizar_perfil_came,
    "calcular_resistencia_came": calcular_resistencia_came,
    "gerar_came_openscad": gerar_came_openscad,
    "gerar_came_svg": gerar_came_svg,
    "sintetizar_came_de_ergonomia": sintetizar_came_de_ergonomia,
    # --- Ergonomia ---
    "get_antropometria": get_antropometria,
    "calcular_faixa_ajuste": calcular_faixa_ajuste,
    "get_amplitude_movimento": get_amplitude_movimento,
    "validar_amplitude_projetada": validar_amplitude_projetada,
    "get_padrao_pegada": get_padrao_pegada,
    "dimensionar_pega": dimensionar_pega,
    "calcular_largura_pegada": calcular_largura_pegada,
    "get_curva_forca": get_curva_forca,
    "gerar_perfil_resistencia_alvo": gerar_perfil_resistencia_alvo,
    "avaliar_curva_resistencia": avaliar_curva_resistencia,
    "calcular_alinhamento_pivo": calcular_alinhamento_pivo,
    "projetar_ergonomia": projetar_ergonomia,
    # --- Orquestração (pipeline completo) ---
    "projetar_maquina": projetar_maquina_params,
    # --- Montagem 3D ---
    "gerar_pecas_maquina": gerar_pecas_maquina,
    "renderizar_svg_3d": renderizar_svg_3d,
    "gerar_visualizador_html": gerar_visualizador_html,
    # --- Academia virtual ---
    "gerar_catalogo_academia": gerar_catalogo_academia,
    "gerar_planta_academia": gerar_planta_academia,
    # --- Projetos de referência (desenhos reais) ---
    "get_projeto_referencia": get_projeto_referencia,
    "listar_padroes_construtivos": listar_padroes_construtivos,
    "get_padrao_biblioteca": get_padrao_biblioteca,
    "listar_biblioteca_padroes": listar_biblioteca_padroes,
}


#: Schemas das tools no formato aceito por APIs de tool-calling.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "calc_momento_fletor",
        "description": (
            "Calcula o momento fletor (torque) em N.m gerado por uma carga "
            "(kg) aplicada na extremidade de uma alavanca de dado comprimento "
            "(mm). Use para dimensionar/validar alavancas de maquinas "
            "articuladas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "forca_kg": {
                    "type": "number",
                    "description": "Massa aplicada na alavanca, em kg.",
                },
                "distancia_alavanca_mm": {
                    "type": "number",
                    "description": "Comprimento do braco de alavanca, em mm.",
                },
            },
            "required": ["forca_kg", "distancia_alavanca_mm"],
        },
    },
    {
        "name": "get_especificacao_metalon",
        "description": (
            "Retorna as propriedades fisicas (peso por metro, momento de "
            "inercia, modulo de secao, limite de escoamento) de um perfil de "
            "metalon comercial para uma espessura de parede."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "perfil": {
                    "type": "string",
                    "description": "Notacao comercial 'BASExALTURA' em mm, ex.: '50x50'.",
                },
                "espessura_parede_mm": {
                    "type": "number",
                    "description": "Espessura de parede em mm, ex.: 1.5, 3.0.",
                },
            },
            "required": ["perfil", "espessura_parede_mm"],
        },
    },
    {
        "name": "validar_resistencia_estrutural",
        "description": (
            "Valida se um perfil de metalon suporta a carga da alavanca. "
            "Calcula a tensao de flexao, compara com a admissivel (escoamento "
            "/ fator de seguranca) e, se reprovado, recomenda a espessura "
            "minima."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "forca_kg": {"type": "number"},
                "distancia_alavanca_mm": {"type": "number"},
                "perfil": {"type": "string"},
                "espessura_parede_mm": {"type": "number"},
                "fator_seguranca": {
                    "type": "number",
                    "description": "Padrao 2.0 se omitido.",
                },
            },
            "required": [
                "forca_kg",
                "distancia_alavanca_mm",
                "perfil",
                "espessura_parede_mm",
            ],
        },
    },
    {
        "name": "recomendar_espessura_minima",
        "description": (
            "Sugere a menor espessura de parede comercial que aprova o perfil "
            "para a carga informada. Retorna None se nenhuma espessura for "
            "suficiente."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "forca_kg": {"type": "number"},
                "distancia_alavanca_mm": {"type": "number"},
                "perfil": {"type": "string"},
                "fator_seguranca": {"type": "number"},
            },
            "required": ["forca_kg", "distancia_alavanca_mm", "perfil"],
        },
    },
    {
        "name": "gerar_script_openscad",
        "description": (
            "Gera o codigo OpenSCAD parametrico (.scad) de uma maquina "
            "articulada a partir de um dicionario de geometria (dimensoes, "
            "perfis e eixos)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "parametros_geometria": {
                    "type": "object",
                    "description": (
                        "Dimensoes e perfis: altura_coluna_mm, "
                        "comprimento_alavanca_mm, perfil_*_mm, "
                        "espessura_parede_mm, diametro_eixo_mm, etc."
                    ),
                }
            },
            "required": ["parametros_geometria"],
        },
    },
    {
        "name": "gerar_memorial_descritivo",
        "description": (
            "Gera o memorial descritivo (lista de cortes e especificacoes / "
            "lista de materiais) em JSON a partir dos parametros de geometria."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "parametros_geometria": {"type": "object"},
                "como_json": {"type": "boolean"},
            },
            "required": ["parametros_geometria"],
        },
    },
    # -------------------------- Geração de imagem -------------------------
    {
        "name": "gerar_preview_svg",
        "description": (
            "Gera um desenho tecnico 2D (vista lateral / blueprint) da "
            "maquina articulada em SVG (Python puro, sem dependencias), "
            "ilustrando base, coluna, pivo, braco e o arco de movimento (ADM)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "parametros_geometria": {"type": "object"},
                "angulo_inicial_graus": {"type": "number"},
                "angulo_final_graus": {"type": "number"},
                "largura_px": {"type": "integer"},
            },
            "required": ["parametros_geometria"],
        },
    },
    {
        "name": "renderizar_openscad_png",
        "description": (
            "Renderiza um arquivo .scad em PNG usando o executavel do "
            "OpenSCAD (requer OpenSCAD instalado). Retorna o caminho do PNG."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "caminho_scad": {"type": "string"},
                "caminho_saida_png": {"type": "string"},
                "tamanho": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "[largura, altura] em px.",
                },
                "camera": {"type": "string"},
                "colorscheme": {"type": "string"},
                "openscad_bin": {"type": "string"},
            },
            "required": ["caminho_scad"],
        },
    },
    {
        "name": "montar_prompt_imagem_produto",
        "description": (
            "Monta o prompt (positivo e negativo) para um modelo de "
            "texto->imagem gerar o render de produto da maquina, a partir da "
            "geometria e (opcional) do envelope ergonomico. Provedor-agnostico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "parametros_geometria": {"type": "object"},
                "envelope_ergonomico": {"type": "object"},
                "estilo": {"type": "string"},
                "idioma": {"type": "string", "enum": ["pt", "en"]},
            },
            "required": ["parametros_geometria"],
        },
    },
    # --------------------- Síntese de came (resistência) ------------------
    {
        "name": "sintetizar_perfil_came",
        "description": (
            "Sintetiza o perfil de uma came de resistencia variavel a partir "
            "da curva de forca de um grupo muscular: o raio efetivo fica "
            "proporcional a forca (r = raio_max x S_norm), casando resistencia "
            "e forca ao longo da ADM. Retorna amostras polares e o poligono XY."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "grupo_muscular": {"type": "string"},
                "raio_max_mm": {"type": "number"},
                "amplitude_movimento_graus": {"type": "number"},
                "n_pontos": {"type": "integer"},
            },
            "required": ["grupo_muscular"],
        },
    },
    {
        "name": "calcular_resistencia_came",
        "description": (
            "Calcula o torque resistente (N.m) produzido pela came para uma "
            "carga (kg), amostrado nos 5 pontos canonicos do movimento — "
            "pronto para reavaliar o casamento com avaliar_curva_resistencia."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "perfil_came": {"type": "object"},
                "carga_kg": {"type": "number"},
            },
            "required": ["perfil_came", "carga_kg"],
        },
    },
    {
        "name": "gerar_came_openscad",
        "description": (
            "Gera o codigo OpenSCAD da came (chapa 2D extrudada) com furo do "
            "eixo no centro e furo de ancoragem do cabo junto ao raio de pico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "perfil_came": {"type": "object"},
                "espessura_mm": {"type": "number"},
                "diametro_eixo_mm": {"type": "number"},
                "diametro_furo_cabo_mm": {"type": "number"},
            },
            "required": ["perfil_came"],
        },
    },
    {
        "name": "gerar_came_svg",
        "description": (
            "Gera um preview 2D (SVG) do perfil da came, sem dependencias."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "perfil_came": {"type": "object"},
                "largura_px": {"type": "integer"},
            },
            "required": ["perfil_came"],
        },
    },
    {
        "name": "sintetizar_came_de_ergonomia",
        "description": (
            "Atalho: sintetiza a came diretamente do envelope de "
            "projetar_ergonomia, usando o grupo muscular e a amplitude de "
            "treino (ADM) do envelope."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "envelope": {"type": "object"},
                "raio_max_mm": {"type": "number"},
                "n_pontos": {"type": "integer"},
            },
            "required": ["envelope"],
        },
    },
    # ---------------------------- Ergonomia -------------------------------
    {
        "name": "get_antropometria",
        "description": (
            "Retorna uma dimensao corporal (mm) por medida, percentil (5-95, "
            "interpolado) e sexo. Ex.: altura_poplitea, comprimento_mao, "
            "largura_biacromial, altura_ombro_sentado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "medida": {"type": "string"},
                "percentil": {"type": "number", "description": "5 a 95. Padrao 50."},
                "sexo": {"type": "string", "enum": ["masculino", "feminino"]},
            },
            "required": ["medida"],
        },
    },
    {
        "name": "calcular_faixa_ajuste",
        "description": (
            "Dimensiona o curso de regulagem de um componente (assento, "
            "encosto...) para acomodar o envelope P5-P95 (mulher P5 a homem "
            "P95, quando sexo='ambos')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "medida": {"type": "string"},
                "percentil_min": {"type": "number"},
                "percentil_max": {"type": "number"},
                "sexo": {"type": "string", "enum": ["masculino", "feminino", "ambos"]},
                "folga_mm": {"type": "number"},
            },
            "required": ["medida"],
        },
    },
    {
        "name": "get_amplitude_movimento",
        "description": (
            "Retorna a amplitude de movimento (graus) anatomica e a "
            "recomendada para treino de uma articulacao/movimento. Ex.: "
            "cotovelo/flexao, joelho/extensao, ombro/abducao."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "articulacao": {"type": "string"},
                "movimento": {"type": "string"},
            },
            "required": ["articulacao", "movimento"],
        },
    },
    {
        "name": "validar_amplitude_projetada",
        "description": (
            "Valida se o arco projetado do braco articulado (angulo inicial e "
            "final, em graus) respeita a ADM de treino; sugere clamp se exceder."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "articulacao": {"type": "string"},
                "movimento": {"type": "string"},
                "angulo_inicial_graus": {"type": "number"},
                "angulo_final_graus": {"type": "number"},
            },
            "required": [
                "articulacao",
                "movimento",
                "angulo_inicial_graus",
                "angulo_final_graus",
            ],
        },
    },
    {
        "name": "get_padrao_pegada",
        "description": (
            "Descreve uma orientacao de punho (pronada/supinada/neutra/mista): "
            "angulo do antebraco e enfase muscular/articular."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "orientacao": {
                    "type": "string",
                    "enum": ["pronada", "supinada", "neutra", "mista"],
                }
            },
            "required": ["orientacao"],
        },
    },
    {
        "name": "dimensionar_pega",
        "description": (
            "Calcula o diametro recomendado da pega cilindrica a partir do "
            "comprimento da mao (via percentil/sexo ou valor direto) e do "
            "objetivo: conforto, forca_preensao ou precisao."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "objetivo": {
                    "type": "string",
                    "enum": ["conforto", "forca_preensao", "precisao"],
                },
                "percentil": {"type": "number"},
                "sexo": {"type": "string", "enum": ["masculino", "feminino"]},
                "comprimento_mao_mm": {"type": "number"},
            },
            "required": [],
        },
    },
    {
        "name": "calcular_largura_pegada",
        "description": (
            "Calcula a distancia entre pegas a partir da largura biacromial "
            "(ombros) e da largura desejada: fechada, media ou aberta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "largura": {
                    "type": "string",
                    "enum": ["fechada", "media", "aberta"],
                },
                "percentil": {"type": "number"},
                "sexo": {"type": "string", "enum": ["masculino", "feminino"]},
                "largura_biacromial_mm": {"type": "number"},
            },
            "required": [],
        },
    },
    {
        "name": "get_curva_forca",
        "description": (
            "Retorna a curva de forca humana normalizada (tipo ascendente/"
            "descendente/sino e perfil em 0-100% do movimento) de um grupo "
            "muscular. Ex.: biceps, triceps, quadriceps, dorsal."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"grupo_muscular": {"type": "string"}},
            "required": ["grupo_muscular"],
        },
    },
    {
        "name": "gerar_perfil_resistencia_alvo",
        "description": (
            "Gera o perfil de resistencia-alvo (kg em cada ponto do movimento) "
            "que acompanha a curva de forca do grupo muscular, dada a carga de "
            "pico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "grupo_muscular": {"type": "string"},
                "carga_pico_kg": {"type": "number"},
            },
            "required": ["grupo_muscular", "carga_pico_kg"],
        },
    },
    {
        "name": "avaliar_curva_resistencia",
        "description": (
            "Avalia (pontuacao 0-100) o quao bem a resistencia da maquina "
            "(perfil amostrado em 5 pontos) acompanha a curva de forca do "
            "grupo muscular, indicando o ponto de maior descasamento."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "perfil_maquina": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Resistencia em 0%,25%,50%,75%,100% do movimento.",
                },
                "grupo_muscular": {"type": "string"},
            },
            "required": ["perfil_maquina", "grupo_muscular"],
        },
    },
    {
        "name": "calcular_alinhamento_pivo",
        "description": (
            "Calcula a altura do eixo de pivo para alinhar com o eixo "
            "anatomico da articulacao, a partir de uma medida antropometrica, "
            "e a faixa de ajuste P5-P95 do componente."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "medida_alinhamento": {"type": "string"},
                "percentil": {"type": "number"},
                "sexo": {"type": "string", "enum": ["masculino", "feminino"]},
            },
            "required": ["medida_alinhamento"],
        },
    },
    {
        "name": "projetar_ergonomia",
        "description": (
            "Integrador: gera o envelope ergonomico completo de um exercicio "
            "do catalogo (alinhamento de pivo, ADM, padrao de pegada completo, "
            "faixas de ajuste do posto e curva de resistencia-alvo). Ex.: "
            "rosca_biceps, cadeira_extensora, supino_maquina."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "exercicio": {"type": "string"},
                "percentil": {"type": "number"},
                "sexo": {"type": "string", "enum": ["masculino", "feminino"]},
                "carga_pico_kg": {"type": "number"},
                "objetivo_pega": {
                    "type": "string",
                    "enum": ["conforto", "forca_preensao", "precisao"],
                },
            },
            "required": ["exercicio"],
        },
    },
    # ------------------------ Orquestração --------------------------------
    {
        "name": "projetar_maquina",
        "description": (
            "Pipeline completo: de um exercicio + parametros a um projeto "
            "validado (ergonomia + came de resistencia variavel + estrutura "
            "com autocorrecao de espessura + geometria OpenSCAD + memorial + "
            "imagem). Retorna tudo, incluindo 'aprovado' e 'resumo'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "exercicio": {"type": "string"},
                "carga_kg": {"type": "number"},
                "percentil": {"type": "number"},
                "sexo": {"type": "string", "enum": ["masculino", "feminino"]},
                "objetivo_pega": {
                    "type": "string",
                    "enum": ["conforto", "forca_preensao", "precisao"],
                },
                "comprimento_alavanca_mm": {"type": "number"},
                "perfil": {"type": "string", "description": "Ex.: '50x50', '60x60'."},
                "fator_seguranca": {"type": "number"},
                "raio_max_came_mm": {"type": "number"},
            },
            "required": ["exercicio"],
        },
    },
    # ------------------------ Montagem 3D ---------------------------------
    {
        "name": "gerar_pecas_maquina",
        "description": (
            "Gera o modelo 3D parametrico da maquina (lista de pecas com "
            "etapa de montagem e direcao de explosao) a partir dos parametros "
            "de geometria. Suporta iso-lateral (2 bracos independentes)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "parametros": {"type": "object"},
                "iso_lateral": {"type": "boolean"},
            },
            "required": [],
        },
    },
    {
        "name": "renderizar_svg_3d",
        "description": (
            "Renderiza o modelo 3D em SVG sombreado (projecao orbitavel): "
            "yaw/pitch de camera, limite de etapa de montagem e vista "
            "explodida (0-1)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "modelo": {"type": "object"},
                "largura_px": {"type": "integer"},
                "yaw_graus": {"type": "number"},
                "pitch_graus": {"type": "number"},
                "etapa_max": {"type": "integer"},
                "explosao": {"type": "number"},
                "titulo": {"type": "string"},
                "subtitulo": {"type": "string"},
            },
            "required": ["modelo"],
        },
    },
    {
        "name": "gerar_visualizador_html",
        "description": (
            "Gera o visualizador 3D interativo auto-contido (HTML+Canvas, sem "
            "dependencias): orbitar, zoom, etapas de montagem e vista "
            "explodida."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "modelo": {"type": "object"},
                "titulo": {"type": "string"},
                "specs_extra": {"type": "object"},
            },
            "required": ["modelo"],
        },
    },
    # ------------------------ Academia virtual ----------------------------
    {
        "name": "gerar_catalogo_academia",
        "description": (
            "Catalogo da academia virtual: os equipamentos mais usados do "
            "mercado (dimensoes reais, musculos, referencia topo de linha) e "
            "quais tem projeto completo no pipeline DechenGym."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "gerar_planta_academia",
        "description": (
            "Planta baixa (SVG, escala real) da academia virtual completa, "
            "com zonas, folgas de circulacao e footprints de mercado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"largura_px": {"type": "integer"}},
            "required": [],
        },
    },
    # ---------------- Projetos de referência (desenhos reais) -------------
    {
        "name": "get_projeto_referencia",
        "description": (
            "Projeto de referencia real (desenhos de fabricacao 201-ABDUTOR, "
            "202-ESTACAO, 203-AGACHAMENTO 60, 204-PECK DECK): arquitetura, "
            "articulacao usinada, regulagens e dimensoes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"nome": {
                "type": "string",
                "enum": ["abdutor_201", "estacao_202", "agachamento_203",
                         "peck_deck_204", "suporte_dumbbells_205",
                         "suporte_barras_206", "suporte_barras_vertical_207",
                         "arco_210"],
            }},
            "required": ["nome"],
        },
    },
    {
        "name": "listar_padroes_construtivos",
        "description": (
            "Padroes construtivos transversais extraidos dos projetos reais "
            "(articulacao usinada, regulagem disco+pino, gussets, borracha, "
            "protecoes, itens comerciais, cortes em angulo)."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_padrao_biblioteca",
        "description": (
            "Componente-padrao da biblioteca de fabrica (01-PADROES: polias, "
            "protetores, buchas, pinos, cremalheiras, estofados, calcos)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"chave": {"type": "string"}},
            "required": ["chave"],
        },
    },
    {
        "name": "listar_biblioteca_padroes",
        "description": (
            "Lista a biblioteca de componentes-padrao (opcionalmente por "
            "categoria: articulacao, polia, protecao, regulagem, engate, "
            "estofado, acabamento, estrutura, came)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"categoria": {"type": "string"}},
            "required": [],
        },
    },
]


def executar_tool(nome: str, argumentos: dict[str, Any]) -> Any:
    """Despacha a execução de uma tool pelo nome.

    Parameters
    ----------
    nome:
        Nome da tool (deve existir em :data:`TOOLS`).
    argumentos:
        Argumentos nomeados a repassar para a função.

    Raises
    ------
    KeyError
        Se a tool não estiver registrada.
    """
    if nome not in TOOLS:
        raise KeyError(f"Tool '{nome}' nao registrada. Disponiveis: {list(TOOLS)}")
    return TOOLS[nome](**argumentos)
