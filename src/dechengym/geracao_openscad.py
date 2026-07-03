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


def parametros_geometria_de_ergonomia(
    envelope: dict[str, Any],
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Converte um envelope ergonômico em parâmetros de geometria.

    Ponte entre o módulo de Ergonomia e a Geração OpenSCAD: mapeia o
    resultado de :func:`dechengym.ergonomia.projetar_ergonomia` para as
    chaves esperadas por :func:`gerar_script_openscad`, garantindo que a
    geometria nasça alinhada às recomendações ergonômicas (altura do pivô,
    diâmetro da pega, etc.).

    Parameters
    ----------
    envelope:
        Saída de ``projetar_ergonomia``.
    extras:
        Sobrescritas/complementos de geometria (perfis, espessura, etc.),
        aplicados por último.

    Returns
    -------
    dict
        Dicionário de ``parametros_geometria`` pronto para a geração.
    """
    altura_pivo = envelope["alinhamento_pivo"]["altura_pivo_mm"]
    diametro_pega = envelope["pegada"]["diametro"]["diametro_recomendado_mm"]

    # O pivô no .scad fica em z = perfil_base + altura_coluna. Para que o eixo
    # coincida com a altura anatômica, descontamos a altura da base.
    perfil_base = float((extras or {}).get("perfil_base_mm", _PARAMETROS_PADRAO["perfil_base_mm"]))
    altura_coluna = max(0.0, altura_pivo - perfil_base)

    parametros: dict[str, Any] = {
        "nome": envelope.get("exercicio", "maquina_articulada"),
        # A coluna leva o eixo de pivô até a altura anatômica da articulação
        # (medida a partir do piso, descontada a altura da base).
        "altura_coluna_mm": altura_coluna,
        "diametro_pega_mm": diametro_pega,
    }
    if extras:
        parametros.update(extras)
    return parametros


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
    // Pega/manopla na extremidade da alavanca (a alavanca se estende em +X).
    color("Crimson")
        translate([base_largura/2 - perfil_alavanca/2 + comprimento_alavanca,
                   base_profundidade/2 - diametro_pega,
                   perfil_base + altura_coluna])
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
    avisos: list[str] = []

    def _peso_por_metro(perfil: str) -> float | None:
        """Peso por metro do perfil quadrado; ``None`` se fora do catálogo."""
        try:
            spec = get_especificacao_metalon(perfil, p["espessura_parede_mm"])
            return spec["peso_por_metro_kg"]
        except (KeyError, ValueError):
            return None  # perfil/espessura fora do catálogo

    def _peca(descricao: str, lado_mm, comprimento_mm: float, quantidade: int) -> dict:
        perfil = f"{int(lado_mm)}x{int(lado_mm)}"
        ppm = _peso_por_metro(perfil)
        estimado = ppm is not None
        if not estimado:
            avisos.append(
                f"Peso nao estimado para '{descricao}': perfil {perfil} parede "
                f"{p['espessura_parede_mm']} mm fora do catalogo de metalon."
            )
        peso_unit = (ppm or 0.0) * (comprimento_mm / 1000.0)
        return {
            "descricao": descricao,
            "perfil": perfil,
            "espessura_parede_mm": p["espessura_parede_mm"],
            "comprimento_corte_mm": round(comprimento_mm, 1),
            "quantidade": quantidade,
            "peso_estimado": estimado,
            "peso_unitario_kg": round(peso_unit, 3) if estimado else None,
            "peso_total_kg": round(peso_unit * quantidade, 3) if estimado else None,
        }

    lista_cortes = [
        _peca("Longarina da base", p["perfil_base_mm"], p["base_profundidade_mm"], 2),
        _peca("Travessa da base", p["perfil_base_mm"], p["base_largura_mm"], 2),
        _peca("Coluna vertical", p["perfil_coluna_mm"], p["altura_coluna_mm"], 1),
        _peca("Braco de alavanca", p["perfil_alavanca_mm"], p["comprimento_alavanca_mm"], 1),
    ]

    peso_estrutura_kg = round(
        sum(item["peso_total_kg"] for item in lista_cortes if item["peso_estimado"]), 3
    )
    peso_completo = all(item["peso_estimado"] for item in lista_cortes)

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
        "peso_total_completo": peso_completo,
        "avisos": avisos,
    }

    if como_json:
        return json.dumps(memorial, indent=2, ensure_ascii=False)
    return memorial
