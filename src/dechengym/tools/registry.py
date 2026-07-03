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

#: Mapa nome -> callable. É a fonte de verdade da execução.
TOOLS: dict[str, Callable[..., Any]] = {
    "calc_momento_fletor": calc_momento_fletor,
    "get_especificacao_metalon": get_especificacao_metalon,
    "validar_resistencia_estrutural": validar_resistencia_estrutural,
    "recomendar_espessura_minima": recomendar_espessura_minima,
    "gerar_script_openscad": gerar_script_openscad,
    "gerar_memorial_descritivo": gerar_memorial_descritivo,
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
