"""
Módulo de Geração OpenSCAD
==========================

Ferramentas (Tools) que transformam um dicionário de parâmetros de
geometria no artefato final do projeto:

- :func:`gerar_script_openscad`   — código `.scad` paramétrico da máquina.
- :func:`gerar_memorial_descritivo` — JSON com a lista de cortes e
  especificações (memorial descritivo / lista de materiais).

O escopo inicial modela uma **máquina articulada** genérica composta por:
base (chassi), coluna vertical, eixo de pivô e braço de alavanca. Toda a
geometria é parametrizada por variáveis no topo do script, de forma que o
mesmo `.scad` possa ser reaproveitado e ajustado no OpenSCAD.
"""

from __future__ import annotations

import json
from typing import Any

# Valores padrão para uma máquina articulada de referência.
_PARAMETROS_PADRAO: dict[str, Any] = {
    "nome": "braco_articulado",
    "perfil_base_mm": 50,          # lado do metalon (assume quadrado) da base
    "perfil_coluna_mm": 60,        # lado do metalon da coluna
    "perfil_alavanca_mm": 50,      # lado do metalon do braço de alavanca
    "espessura_parede_mm": 3.0,
    "altura_coluna_mm": 1200,
    "comprimento_alavanca_mm": 800,
    "base_largura_mm": 700,
    "base_profundidade_mm": 700,
    "diametro_eixo_mm": 25,        # eixo de pivô
    "diametro_pega_mm": 30,        # pega/manopla na extremidade
    "resolucao_fn": 64,            # $fn dos cilindros
}


def _merge_parametros(parametros_geometria: dict[str, Any] | None) -> dict[str, Any]:
    """Combina os parâmetros recebidos com os padrões (recebidos vencem)."""
    p = dict(_PARAMETROS_PADRAO)
    if parametros_geometria:
        p.update(parametros_geometria)
    return p


# ==========================================================================
# Tool 5 — Geração do script OpenSCAD
# ==========================================================================
def gerar_script_openscad(parametros_geometria: dict[str, Any] | None = None) -> str:
    """Gera o código OpenSCAD paramétrico de uma máquina articulada.

    Recebe os eixos e dimensões e "cospe" o código paramétrico do
    equipamento. Parâmetros omitidos assumem valores padrão de referência
    (:data:`_PARAMETROS_PADRAO`).

    Parameters
    ----------
    parametros_geometria:
        Dicionário com chaves como ``altura_coluna_mm``,
        ``comprimento_alavanca_mm``, ``perfil_*_mm``, ``diametro_eixo_mm``,
        etc. Veja :data:`_PARAMETROS_PADRAO`.

    Returns
    -------
    str
        Conteúdo completo de um arquivo ``.scad``.
    """
    p = _merge_parametros(parametros_geometria)

    scad = f"""// ==========================================================================
// DechenGym - Maquina articulada: {p["nome"]}
// Script OpenSCAD gerado automaticamente (geometria parametrica).
// Unidades: milimetros (mm).
// ==========================================================================

// ------------------------- Parametros -------------------------------------
perfil_base      = {p["perfil_base_mm"]};      // lado do metalon da base
perfil_coluna    = {p["perfil_coluna_mm"]};    // lado do metalon da coluna
perfil_alavanca  = {p["perfil_alavanca_mm"]};  // lado do metalon da alavanca
espessura_parede = {p["espessura_parede_mm"]}; // espessura da parede do tubo

altura_coluna       = {p["altura_coluna_mm"]};
comprimento_alavanca= {p["comprimento_alavanca_mm"]};
base_largura        = {p["base_largura_mm"]};
base_profundidade   = {p["base_profundidade_mm"]};

diametro_eixo = {p["diametro_eixo_mm"]};  // eixo de pivo
diametro_pega = {p["diametro_pega_mm"]};  // manopla

$fn = {p["resolucao_fn"]};

// ------------------------- Modulos utilitarios ----------------------------

// Tubo metalon (secao quadrada vazada) ao longo do eixo Z.
module metalon(lado, comprimento, parede) {{
    difference() {{
        cube([lado, lado, comprimento]);
        translate([parede, parede, -1])
            cube([lado - 2 * parede, lado - 2 * parede, comprimento + 2]);
    }}
}}

// Eixo cilindrico (pivo/pega) ao longo do eixo X.
module eixo_x(diametro, comprimento) {{
    rotate([0, 90, 0])
        cylinder(h = comprimento, d = diametro);
}}

// ------------------------- Montagem ---------------------------------------

module base() {{
    // Dois perfis longitudinais formando o chassi da base.
    color("SlateGray") {{
        rotate([-90, 0, 0])
            metalon(perfil_base, base_profundidade, espessura_parede);
        translate([base_largura - perfil_base, 0, 0])
            rotate([-90, 0, 0])
                metalon(perfil_base, base_profundidade, espessura_parede);
        // Travessa frontal e traseira.
        rotate([0, 90, 0])
            metalon(perfil_base, base_largura, espessura_parede);
        translate([0, base_profundidade - perfil_base, 0])
            rotate([0, 90, 0])
                metalon(perfil_base, base_largura, espessura_parede);
    }}
}}

module coluna() {{
    // Coluna vertical central, a partir do topo da base.
    color("DimGray")
        translate([base_largura/2 - perfil_coluna/2,
                   base_profundidade/2 - perfil_coluna/2,
                   perfil_base])
            metalon(perfil_coluna, altura_coluna, espessura_parede);
}}

module pivo() {{
    // Eixo de pivo no topo da coluna.
    color("Goldenrod")
        translate([base_largura/2 - perfil_coluna,
                   base_profundidade/2,
                   perfil_base + altura_coluna])
            eixo_x(diametro_eixo, perfil_coluna * 2);
}}

module alavanca() {{
    // Braco de alavanca articulado, saindo do eixo de pivo.
    color("SteelBlue")
        translate([base_largura/2 - perfil_alavanca/2,
                   base_profundidade/2 - perfil_alavanca/2,
                   perfil_base + altura_coluna])
            rotate([0, 90, 0])
                metalon(perfil_alavanca, comprimento_alavanca, espessura_parede);
    // Pega/manopla na extremidade da alavanca.
    color("Crimson")
        translate([base_largura/2 - perfil_alavanca/2,
                   base_profundidade/2 - diametro_pega,
                   perfil_base + altura_coluna + comprimento_alavanca])
            eixo_x(diametro_pega, diametro_pega * 3);
}}

module maquina_articulada() {{
    base();
    coluna();
    pivo();
    alavanca();
}}

maquina_articulada();
"""
    return scad


# ==========================================================================
# Tool 6 — Memorial descritivo (lista de cortes / especificacoes)
# ==========================================================================
def gerar_memorial_descritivo(
    parametros_geometria: dict[str, Any] | None = None,
    *,
    como_json: bool = False,
) -> dict[str, Any] | str:
    """Gera o memorial descritivo (lista de cortes e especificações).

    Enumera cada peça estrutural da máquina com perfil, comprimento de corte,
    quantidade e peso estimado — servindo como lista de materiais para a
    fabricação.

    Parameters
    ----------
    parametros_geometria:
        Mesmos parâmetros de :func:`gerar_script_openscad`.
    como_json:
        Se ``True``, retorna uma *string* JSON formatada; caso contrário,
        retorna o ``dict``.

    Returns
    -------
    dict | str
        Memorial descritivo estruturado (dict) ou sua serialização JSON.
    """
    # Importação local evita ciclo de import no carregamento do pacote.
    from dechengym.calculo_estrutural import get_especificacao_metalon

    p = _merge_parametros(parametros_geometria)

    def _peso_por_metro(lado_mm: int | float) -> float:
        """Peso por metro do perfil quadrado, via especificação de metalon."""
        perfil = f"{int(lado_mm)}x{int(lado_mm)}"
        try:
            spec = get_especificacao_metalon(perfil, p["espessura_parede_mm"])
            return spec["peso_por_metro_kg"]
        except (KeyError, ValueError):
            return 0.0  # perfil/espessura fora do catálogo: peso não estimado

    def _peca(descricao: str, lado_mm, comprimento_mm: float, quantidade: int) -> dict:
        peso_unit = _peso_por_metro(lado_mm) * (comprimento_mm / 1000.0)
        return {
            "descricao": descricao,
            "perfil": f"{int(lado_mm)}x{int(lado_mm)}",
            "espessura_parede_mm": p["espessura_parede_mm"],
            "comprimento_corte_mm": round(comprimento_mm, 1),
            "quantidade": quantidade,
            "peso_unitario_kg": round(peso_unit, 3),
            "peso_total_kg": round(peso_unit * quantidade, 3),
        }

    lista_cortes = [
        _peca("Longarina da base", p["perfil_base_mm"], p["base_profundidade_mm"], 2),
        _peca("Travessa da base", p["perfil_base_mm"], p["base_largura_mm"], 2),
        _peca("Coluna vertical", p["perfil_coluna_mm"], p["altura_coluna_mm"], 1),
        _peca("Braco de alavanca", p["perfil_alavanca_mm"], p["comprimento_alavanca_mm"], 1),
    ]

    peso_estrutura_kg = round(sum(item["peso_total_kg"] for item in lista_cortes), 3)

    memorial: dict[str, Any] = {
        "projeto": p["nome"],
        "tipo": "maquina_articulada",
        "unidades": "mm / kg",
        "parametros": {
            "altura_coluna_mm": p["altura_coluna_mm"],
            "comprimento_alavanca_mm": p["comprimento_alavanca_mm"],
            "espessura_parede_mm": p["espessura_parede_mm"],
        },
        "componentes_nao_estruturais": [
            {
                "descricao": "Eixo de pivo",
                "tipo": "barra_redonda",
                "diametro_mm": p["diametro_eixo_mm"],
                "quantidade": 1,
            },
            {
                "descricao": "Pega / manopla",
                "tipo": "barra_redonda",
                "diametro_mm": p["diametro_pega_mm"],
                "quantidade": 1,
            },
        ],
        "lista_cortes": lista_cortes,
        "peso_total_estrutura_kg": peso_estrutura_kg,
    }

    if como_json:
        return json.dumps(memorial, indent=2, ensure_ascii=False)
    return memorial
