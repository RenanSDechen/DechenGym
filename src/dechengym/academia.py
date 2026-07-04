"""
Academia Virtual
================

Monta a academia virtual a partir da base
:mod:`dechengym.data.academia_db`:

- :func:`gerar_planta_academia` — **planta baixa** (SVG, vista superior) com
  os equipamentos posicionados por zona, corredores de circulação de
  0,60 m entre máquinas e 1,20 m entre zonas, e legenda por categoria.
- :func:`gerar_catalogo_academia` — catálogo estruturado (para interface,
  relatórios e Tool Calling), indicando quais equipamentos têm **projeto
  completo** no pipeline DechenGym.
"""

from __future__ import annotations

from typing import Any

from dechengym.data.academia_db import (
    ACADEMIA_VIRTUAL,
    categorias,
    equipamentos_da_categoria,
    resumo_academia,
)

_CORES_ZONA = {
    "Musculacao articulada (plate-loaded)": ("#c1272d", "#fdecea"),
    "Musculacao seletorizada (polia/placas)": ("#1d4ed8", "#e8eefc"),
    "Pernas (guiadas e prensas)": ("#15803d", "#e9f7ee"),
    "Peso livre e bancos": ("#a16207", "#fdf6e3"),
    "Cardio": ("#6d28d9", "#f1ecfb"),
}

FOLGA_MAQUINA_MM = 600.0   # circulação mínima entre máquinas
FOLGA_ZONA_MM = 1200.0     # corredor entre zonas


def gerar_catalogo_academia() -> dict[str, Any]:
    """Catálogo estruturado da academia virtual (por categoria)."""
    cat: dict[str, Any] = {"resumo": resumo_academia(), "categorias": []}
    for c in categorias():
        itens = []
        for chave, e in equipamentos_da_categoria(c):
            itens.append({
                "id": chave,
                "nome": e["nome"],
                "tipo": e["tipo"],
                "musculos": e["musculos"],
                "footprint_mm": e["footprint_mm"],
                "altura_mm": e["altura_mm"],
                "carga_max_kg": e["carga_max_kg"],
                "referencia": e["referencia"],
                "rank": e["rank"],
                "projeto_completo": e["exercicio_pipeline"] is not None,
                "exercicio_pipeline": e["exercicio_pipeline"],
            })
        cat["categorias"].append({"categoria": c, "equipamentos": itens})
    return cat


def _layout_zonas() -> tuple[list[dict[str, Any]], float, float]:
    """Posiciona os equipamentos: zonas em faixas horizontais; dentro da
    zona, máquinas lado a lado com quebra de linha (folga de 600 mm)."""
    LARGURA_SALAO = 15000.0  # 15 m de frente
    itens: list[dict[str, Any]] = []
    y = FOLGA_ZONA_MM
    for c in categorias():
        maquinas = equipamentos_da_categoria(c)
        x = FOLGA_ZONA_MM
        alt_linha = 0.0
        y_zona_ini = y
        for chave, e in maquinas:
            w, d = float(e["footprint_mm"][0]), float(e["footprint_mm"][1])
            if x + w > LARGURA_SALAO - FOLGA_ZONA_MM:
                x = FOLGA_ZONA_MM
                y += alt_linha + FOLGA_MAQUINA_MM
                alt_linha = 0.0
            itens.append({"id": chave, "nome": e["nome"], "categoria": c,
                          "x": x, "y": y, "w": w, "d": d,
                          "projeto": e["exercicio_pipeline"] is not None})
            x += w + FOLGA_MAQUINA_MM
            alt_linha = max(alt_linha, d)
        y += alt_linha + FOLGA_ZONA_MM
        for it in itens:
            if it["categoria"] == c:
                it.setdefault("y_zona", y_zona_ini)
    return itens, LARGURA_SALAO, y


def gerar_planta_academia(largura_px: int = 1180) -> str:
    """Gera a planta baixa (SVG) da academia virtual completa.

    Vista superior com escala real: cada retângulo é o footprint de mercado
    do equipamento; folgas de 0,60 m entre máquinas e 1,20 m entre zonas.
    Equipamentos com **projeto completo DechenGym** recebem borda destacada.
    """
    itens, larg_mm, prof_mm = _layout_zonas()
    esc = (largura_px - 40) / larg_mm
    alt_px = int(prof_mm * esc) + 120

    corpo: list[str] = []
    # Zonas (faixas de fundo)
    zonas: dict[str, list[float]] = {}
    for it in itens:
        z = zonas.setdefault(it["categoria"], [1e12, -1e12])
        z[0] = min(z[0], it["y"] - 300)
        z[1] = max(z[1], it["y"] + it["d"] + 300)
    for c, (y0, y1) in zonas.items():
        cor_f = _CORES_ZONA[c][1]
        corpo.append(
            f'<rect x="20" y="{20 + y0 * esc:.0f}" width="{largura_px - 40}" '
            f'height="{(y1 - y0) * esc:.0f}" fill="{cor_f}" rx="8"/>'
        )
        corpo.append(
            f'<text x="30" y="{20 + y0 * esc + 15:.0f}" font-family="Helvetica" '
            f'font-size="12" font-weight="bold" fill="{_CORES_ZONA[c][0]}">{c}</text>'
        )
    # Equipamentos
    for it in itens:
        cor = _CORES_ZONA[it["categoria"]][0]
        x, y = 20 + it["x"] * esc, 20 + it["y"] * esc
        w, d = it["w"] * esc, it["d"] * esc
        borda = f'stroke="{cor}" stroke-width="3"' if it["projeto"] else f'stroke="{cor}" stroke-width="1" stroke-dasharray="4 3"'
        corpo.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{d:.0f}" fill="{cor}" fill-opacity="0.18" {borda} rx="4"/>')
        nome = it["nome"].split("(")[0].strip()
        if len(nome) > 24:
            nome = nome[:23] + "…"
        corpo.append(
            f'<text x="{x + w / 2:.0f}" y="{y + d / 2 + 3:.0f}" text-anchor="middle" '
            f'font-family="Helvetica" font-size="9.5" fill="#1a1f27">{nome}</text>'
        )
        corpo.append(
            f'<text x="{x + w / 2:.0f}" y="{y + d / 2 + 14:.0f}" text-anchor="middle" '
            f'font-family="Helvetica" font-size="7.5" fill="#5b6572">'
            f'{it["w"] / 1000:.1f} x {it["d"] / 1000:.1f} m</text>'
        )

    res = resumo_academia()
    rodape = (
        f"{res['total_equipamentos']} equipamentos · "
        f"{res['com_projeto_completo']} com projeto completo DechenGym (borda cheia) · "
        f"salao {larg_mm / 1000:.0f} x {prof_mm / 1000:.1f} m · "
        f"circulacao 0,60 m entre maquinas e 1,20 m entre zonas"
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura_px}" height="{alt_px}" viewBox="0 0 {largura_px} {alt_px}">
<rect width="100%" height="100%" fill="#ffffff"/>
<rect x="20" y="20" width="{largura_px - 40}" height="{alt_px - 90}" fill="none" stroke="#1a1f27" stroke-width="3"/>
{"".join(corpo)}
<text x="20" y="{alt_px - 46}" font-family="Helvetica" font-size="15" font-weight="bold" fill="#1a1f27">DechenGym — Academia Virtual (planta baixa em escala)</text>
<text x="20" y="{alt_px - 28}" font-family="Helvetica" font-size="10.5" fill="#5b6572">{rodape}</text>
</svg>'''
