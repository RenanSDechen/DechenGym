"""
Módulo de Síntese de Came (braço de momento variável).
=====================================================

Transforma a **curva de força humana** em **geometria real**: gera o perfil
da came cujo raio efetivo faz a resistência sentida acompanhar a força do
músculo ao longo de toda a amplitude de movimento (ADM). É o diferencial
ergonômico do projeto convertido em uma peça fabricável.

Fundamento
----------
Em uma máquina com came acionada por pilha de pesos, a tração no cabo é
aproximadamente constante ``W = m·g``. O torque resistente sobre o eixo é::

    τ(θ) = W · r(θ)

onde ``r(θ)`` é o braço de momento efetivo — o raio da came no ângulo θ.
Para manter a intensidade relativa constante (a máquina "pesa" na proporção
da sua força em cada ponto), queremos ``τ(θ) ∝ S(θ)``, logo::

    r(θ) = r_max · S_norm(θ)

com ``S_norm`` sendo a curva de força normalizada pelo pico (0–1). O raio é,
portanto, **literalmente proporcional à curva de força** — o pico de raio
(máxima resistência) coincide com o ponto de maior força.

Ferramentas expostas
--------------------
- :func:`sintetizar_perfil_came`     — gera o perfil (polar + polígono XY).
- :func:`calcular_resistencia_came`  — torque resultante τ(θ) da came.
- :func:`gerar_came_openscad`        — código OpenSCAD da came (peça 2D
  extrudada, furo do eixo e furo de fixação do cabo).
- :func:`gerar_came_svg`             — preview 2D do perfil da came.
- :func:`sintetizar_came_de_ergonomia` — atalho a partir do envelope
  ergonômico (:func:`dechengym.ergonomia.projetar_ergonomia`).
"""

from __future__ import annotations

import math
import xml.sax.saxutils as _xml
from typing import Any

from dechengym.config import GRAVIDADE_MS2
from dechengym.ergonomia.curva_resistencia import get_curva_forca

# Amostragem padrão do perfil. n-1 múltiplo de 4 garante que os pontos
# canônicos (0/25/50/75/100%) caiam exatamente sobre nós da malha, tornando
# o round-trip (síntese → resistência → avaliação) exato.
_N_PONTOS_PADRAO = 49


def _interp_curva(perfil5: list[float], pct: float) -> float:
    """Interpola a curva de força (5 amostras em 0/25/50/75/100%) num pct."""
    pct = max(0.0, min(100.0, pct))
    passo = 100.0 / (len(perfil5) - 1)  # 25.0
    idx = pct / passo
    i = int(math.floor(idx))
    if i >= len(perfil5) - 1:
        return float(perfil5[-1])
    frac = idx - i
    return float(perfil5[i] + frac * (perfil5[i + 1] - perfil5[i]))


# ==========================================================================
# Tool 10 — Síntese do perfil da came
# ==========================================================================
def sintetizar_perfil_came(
    grupo_muscular: str,
    raio_max_mm: float = 100.0,
    amplitude_movimento_graus: float = 120.0,
    n_pontos: int = _N_PONTOS_PADRAO,
) -> dict[str, Any]:
    """Sintetiza o perfil da came a partir da curva de força do músculo.

    Parameters
    ----------
    grupo_muscular:
        Grupo cuja curva de força define o formato da came (ex.: ``"biceps"``).
    raio_max_mm:
        Raio efetivo no ponto de maior força (define a resistência de pico).
    amplitude_movimento_graus:
        Rotação da came ao longo da ADM (a came gira solidária ao braço).
    n_pontos:
        Número de amostras da superfície de trabalho.

    Returns
    -------
    dict
        ``{"grupo_muscular", "tipo_curva", "raio_max_mm", "raio_min_mm",
        "amplitude_graus", "amostras_trabalho", "poligono_xy"}``.

        - ``amostras_trabalho``: lista de ``{movement_pct, angulo_graus,
          raio_mm}`` da superfície onde o cabo trabalha.
        - ``poligono_xy``: polígono **fechado** (superfície de trabalho +
          arco base) pronto para extrusão/renderização, com o eixo no
          origem (0, 0).

    Raises
    ------
    ValueError
        Se ``raio_max_mm`` ou ``amplitude_movimento_graus`` não forem positivos.
    """
    if raio_max_mm <= 0:
        raise ValueError("raio_max_mm deve ser positivo.")
    if not 0 < amplitude_movimento_graus <= 360:
        raise ValueError("amplitude_movimento_graus deve estar em (0, 360].")
    if n_pontos < 3:
        raise ValueError("n_pontos deve ser >= 3.")

    curva = get_curva_forca(grupo_muscular)
    perfil5 = list(curva["perfil"])
    s_min = min(perfil5)  # como o pico é 1.0, s_min = raio_min/raio_max
    raio_min_mm = raio_max_mm * s_min

    amostras: list[dict[str, float]] = []
    poligono: list[list[float]] = []

    # 1) Superfície de trabalho: r(θ) = raio_max × S_norm ao longo da ADM.
    for k in range(n_pontos):
        pct = 100.0 * k / (n_pontos - 1)
        s = _interp_curva(perfil5, pct)
        raio = raio_max_mm * s
        ang = amplitude_movimento_graus * (pct / 100.0)
        rad = math.radians(ang)
        amostras.append(
            {
                "movement_pct": round(pct, 3),
                "angulo_graus": round(ang, 3),
                "raio_mm": round(raio, 4),
            }
        )
        poligono.append([round(raio * math.cos(rad), 4), round(raio * math.sin(rad), 4)])

    # 2) Arco base (região não-trabalho) fechando a peça com raio mínimo.
    ang = amplitude_movimento_graus
    passo_base = 15.0
    while ang < 360.0 - 1e-6:
        ang = min(ang + passo_base, 360.0)
        rad = math.radians(ang)
        poligono.append(
            [round(raio_min_mm * math.cos(rad), 4), round(raio_min_mm * math.sin(rad), 4)]
        )

    return {
        "grupo_muscular": grupo_muscular,
        "tipo_curva": curva["tipo"],
        "raio_max_mm": round(raio_max_mm, 3),
        "raio_min_mm": round(raio_min_mm, 3),
        "amplitude_graus": amplitude_movimento_graus,
        "amostras_trabalho": amostras,
        "poligono_xy": poligono,
    }


# ==========================================================================
# Tool 11 — Resistência resultante da came
# ==========================================================================
def calcular_resistencia_came(
    perfil_came: dict[str, Any], carga_kg: float
) -> dict[str, Any]:
    """Calcula o torque resistente τ(θ) = W·r(θ) produzido pela came.

    Amostra a resistência nos mesmos 5 pontos canônicos da curva de força
    (0/25/50/75/100% do movimento), de modo que o resultado possa ser
    reavaliado por
    :func:`dechengym.ergonomia.avaliar_curva_resistencia` para confirmar o
    casamento com a curva de força humana.

    Parameters
    ----------
    perfil_came:
        Saída de :func:`sintetizar_perfil_came`.
    carga_kg:
        Massa na pilha de pesos (tração do cabo ``W = carga·g``).

    Returns
    -------
    dict
        ``{"grupo_muscular", "carga_kg", "amostras_pct",
        "raio_amostrado_mm", "torque_nm", "torque_pico_nm"}``.
    """
    if carga_kg < 0:
        raise ValueError("carga_kg nao pode ser negativa.")

    amostras = perfil_came["amostras_trabalho"]
    pcts = [a["movement_pct"] for a in amostras]
    raios = [a["raio_mm"] for a in amostras]

    def _raio_em(pct: float) -> float:
        # Interpolação linear sobre a malha densa da superfície de trabalho.
        if pct <= pcts[0]:
            return raios[0]
        if pct >= pcts[-1]:
            return raios[-1]
        for i in range(len(pcts) - 1):
            if pcts[i] <= pct <= pcts[i + 1]:
                frac = (pct - pcts[i]) / (pcts[i + 1] - pcts[i])
                return raios[i] + frac * (raios[i + 1] - raios[i])
        return raios[-1]

    canonicos = [0, 25, 50, 75, 100]
    forca_n = carga_kg * GRAVIDADE_MS2
    raio_amostrado = [round(_raio_em(p), 4) for p in canonicos]
    # τ = W(N) · r(m)  → N·m
    torque = [round(forca_n * (r / 1000.0), 4) for r in raio_amostrado]

    return {
        "grupo_muscular": perfil_came["grupo_muscular"],
        "carga_kg": carga_kg,
        "amostras_pct": canonicos,
        "raio_amostrado_mm": raio_amostrado,
        "torque_nm": torque,
        "torque_pico_nm": round(max(torque), 4),
    }


# ==========================================================================
# Tool 12 — Geração OpenSCAD da came
# ==========================================================================
def gerar_came_openscad(
    perfil_came: dict[str, Any],
    espessura_mm: float = 12.0,
    diametro_eixo_mm: float = 25.0,
    diametro_furo_cabo_mm: float = 8.0,
) -> str:
    """Gera o código OpenSCAD da came (chapa 2D extrudada).

    Emite o polígono sintetizado extrudado à espessura da chapa, com o furo
    do eixo no centro (pivô) e um furo para ancoragem do cabo próximo ao
    raio máximo.

    Returns
    -------
    str
        Conteúdo de um arquivo ``.scad``.
    """
    pts = perfil_came["poligono_xy"]
    pts_scad = ",\n        ".join(f"[{x}, {y}]" for x, y in pts)

    # Ponto de ancoragem do cabo: extremidade de maior raio da superfície.
    a_pico = max(perfil_came["amostras_trabalho"], key=lambda a: a["raio_mm"])
    rad = math.radians(a_pico["angulo_graus"])
    # Um pouco para dentro do raio de pico, para deixar material na borda.
    r_furo = max(a_pico["raio_mm"] - max(diametro_furo_cabo_mm, 10.0), 0.0)
    furo_x = round(r_furo * math.cos(rad), 3)
    furo_y = round(r_furo * math.sin(rad), 3)

    return f"""// ==========================================================================
// DechenGym - Came de resistencia variavel ({perfil_came["grupo_muscular"]})
// Raio efetivo proporcional a curva de forca (tipo: {perfil_came["tipo_curva"]}).
// Raio de pico: {perfil_came["raio_max_mm"]} mm | raio base: {perfil_came["raio_min_mm"]} mm.
// Amplitude: {perfil_came["amplitude_graus"]} graus. Eixo na origem (0,0). Unidades: mm.
// ==========================================================================

espessura        = {espessura_mm};
diametro_eixo    = {diametro_eixo_mm};
diametro_cabo    = {diametro_furo_cabo_mm};

module came() {{
    linear_extrude(height = espessura) {{
        difference() {{
            polygon(points = [
        {pts_scad}
            ]);
            // Furo do eixo (pivo) no centro de rotacao.
            circle(d = diametro_eixo, $fn = 64);
            // Furo de ancoragem do cabo, junto ao raio de pico.
            translate([{furo_x}, {furo_y}])
                circle(d = diametro_cabo, $fn = 32);
        }}
    }}
}}

came();
"""


# ==========================================================================
# Preview SVG do perfil da came
# ==========================================================================
def gerar_came_svg(perfil_came: dict[str, Any], largura_px: int = 420) -> str:
    """Gera um preview 2D (SVG) do perfil da came, sem dependências."""
    pts = perfil_came["poligono_xy"]
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    margem = 30.0
    esc = (largura_px - 2 * margem) / max(max_x - min_x, 1.0)
    altura_px = int(2 * margem + (max_y - min_y) * esc)

    def w2s(x: float, y: float) -> tuple[float, float]:
        return (margem + (x - min_x) * esc, margem + (max_y - y) * esc)

    caminho = " ".join(
        f"{'M' if i == 0 else 'L'}{w2s(x, y)[0]:.1f},{w2s(x, y)[1]:.1f}"
        for i, (x, y) in enumerate(pts)
    )
    cx, cy = w2s(0.0, 0.0)  # eixo (pivô)

    titulo = _xml.escape(
        f"Came {perfil_came['grupo_muscular']} "
        f"(R {perfil_came['raio_min_mm']:.0f}-{perfil_came['raio_max_mm']:.0f} mm)"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura_px}" '
        f'height="{altura_px}" viewBox="0 0 {largura_px} {altura_px}">\n'
        f'<rect width="100%" height="100%" fill="#f7f9fb"/>\n'
        f'<path d="{caminho} Z" fill="#93c5fd" stroke="#1d4ed8" stroke-width="2"/>\n'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="#f59e0b" '
        f'stroke="#78350f" stroke-width="1.5"/>\n'
        f'<text x="{margem:.0f}" y="18" font-family="sans-serif" font-size="13" '
        f'font-weight="bold" fill="#111827">{titulo}</text>\n'
        f"</svg>"
    )


# ==========================================================================
# Atalho: síntese a partir do envelope ergonômico
# ==========================================================================
def sintetizar_came_de_ergonomia(
    envelope: dict[str, Any],
    raio_max_mm: float = 100.0,
    n_pontos: int = _N_PONTOS_PADRAO,
) -> dict[str, Any]:
    """Sintetiza a came diretamente do envelope de :func:`projetar_ergonomia`.

    Usa o grupo muscular e a amplitude de treino (ADM) do envelope, garantindo
    coerência entre a ergonomia projetada e a came gerada.
    """
    grupo = envelope["grupo_muscular"]
    adm = envelope["amplitude_movimento"]["adm_treino"]
    amplitude = float(adm[1] - adm[0])
    return sintetizar_perfil_came(
        grupo, raio_max_mm=raio_max_mm, amplitude_movimento_graus=amplitude,
        n_pontos=n_pontos,
    )
