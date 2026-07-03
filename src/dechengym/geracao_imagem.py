"""
Módulo de Geração de Imagem
===========================

Ferramentas (Tools) para produzir a **imagem do produto** em três trilhas
complementares, do esquemático ao fotorrealista:

- :func:`gerar_preview_svg`        — desenho técnico 2D (vista lateral /
  blueprint) da máquina articulada. **Python puro, sem dependências** —
  sempre disponível e determinístico.
- :func:`renderizar_openscad_png`  — render 3D em PNG chamando o executável
  do OpenSCAD (quando instalado no ambiente).
- :func:`montar_prompt_imagem_produto` — monta o *prompt* descritivo para um
  modelo de texto→imagem (render de produto), a ser chamado pelo agente
  orquestrador (provedor-agnóstico).

A vista lateral do SVG usa o plano vertical (profundidade × altura) da
máquina e ilustra o **arco de movimento** do braço articulado (ADM),
conectando o projeto ergonômico à representação visual.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from dechengym.geracao_openscad import _merge_parametros


# ==========================================================================
# Utilitários de projeção 2D (vista lateral: eixo Y = profundidade, Z = altura)
# ==========================================================================
def _lever_end(yp: float, zp: float, comprimento: float, angulo_graus: float) -> tuple[float, float]:
    """Ponta do braço de alavanca para um ângulo (graus a partir da horizontal)."""
    rad = math.radians(angulo_graus)
    return (yp - comprimento * math.cos(rad), zp + comprimento * math.sin(rad))


def _svg_escape(texto: str) -> str:
    return (
        texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


# ==========================================================================
# Tool 7 — Preview técnico em SVG (blueprint)
# ==========================================================================
def gerar_preview_svg(
    parametros_geometria: dict[str, Any] | None = None,
    *,
    angulo_inicial_graus: float = 10,
    angulo_final_graus: float = 70,
    largura_px: int = 720,
) -> str:
    """Gera um desenho técnico 2D (vista lateral) da máquina em SVG.

    Representa base, coluna, eixo de pivô, braço de alavanca (nas posições
    inicial e final) e o arco de movimento entre elas — um blueprint
    esquemático útil para revisão rápida do projeto, sem qualquer
    dependência externa.

    Parameters
    ----------
    parametros_geometria:
        Mesmos parâmetros de :func:`dechengym.gerar_script_openscad`.
    angulo_inicial_graus, angulo_final_graus:
        Ângulos (a partir da horizontal) das posições inicial e final do
        braço, ilustrando a amplitude de movimento.
    largura_px:
        Largura do SVG em pixels (a altura é calculada proporcionalmente).

    Returns
    -------
    str
        Documento SVG completo (string).
    """
    p = _merge_parametros(parametros_geometria)

    pb = float(p["perfil_base_mm"])
    pc = float(p["perfil_coluna_mm"])
    prof = float(p["base_profundidade_mm"])
    altura_coluna = float(p["altura_coluna_mm"])
    comprimento = float(p["comprimento_alavanca_mm"])
    diam_pega = float(p["diametro_pega_mm"])

    # Pontos-chave em coordenadas de mundo (mm): y = profundidade, z = altura.
    yp, zp = prof / 2.0, pb + altura_coluna  # eixo de pivô
    ang_min = min(angulo_inicial_graus, angulo_final_graus)
    ang_max = max(angulo_inicial_graus, angulo_final_graus)
    end_ini = _lever_end(yp, zp, comprimento, ang_min)
    end_fim = _lever_end(yp, zp, comprimento, ang_max)

    # Bounding box de todo o conteúdo (inclui varredura do braço).
    xs = [0.0, prof, yp, end_ini[0], end_fim[0]]
    zs = [0.0, zp, end_ini[1], end_fim[1]]
    min_y, max_y = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)

    margem = 60.0
    escala = (largura_px - 2 * margem) / max(max_y - min_y, 1.0)
    altura_px = int(2 * margem + (max_z - min_z) * escala)

    def w2s(y: float, z: float) -> tuple[float, float]:
        """Mundo (mm) -> SVG (px), com Y invertido."""
        return (
            margem + (y - min_y) * escala,
            margem + (max_z - z) * escala,
        )

    partes: list[str] = []
    partes.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura_px}" '
        f'height="{altura_px}" viewBox="0 0 {largura_px} {altura_px}">'
    )
    partes.append('<rect width="100%" height="100%" fill="#f7f9fb"/>')

    # Base (chassi) ---------------------------------------------------------
    partes.append(
        f'<rect x="{w2s(0, pb)[0]:.1f}" y="{w2s(0, pb)[1]:.1f}" '
        f'width="{prof * escala:.1f}" height="{pb * escala:.1f}" '
        f'fill="#8a94a6" stroke="#5a6272" stroke-width="1.5"/>'
    )

    # Coluna vertical -------------------------------------------------------
    cx, cy = w2s(yp - pc / 2, zp)
    partes.append(
        f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{pc * escala:.1f}" '
        f'height="{altura_coluna * escala:.1f}" fill="#6b7280" '
        f'stroke="#454b57" stroke-width="1.5"/>'
    )

    # Arco de movimento (ADM) — polilinha tracejada -------------------------
    n = 24
    pts_arco = []
    for i in range(n + 1):
        ang = ang_min + (ang_max - ang_min) * i / n
        ex, ez = _lever_end(yp, zp, comprimento, ang)
        sx, sy = w2s(ex, ez)
        pts_arco.append(f"{sx:.1f},{sy:.1f}")
    partes.append(
        f'<polyline points="{" ".join(pts_arco)}" fill="none" '
        f'stroke="#16a34a" stroke-width="1.5" stroke-dasharray="6 5"/>'
    )

    # Braço de alavanca: posição inicial (fantasma) e final (sólida) --------
    px_pivo, py_pivo = w2s(yp, zp)
    for (ex, ez), cor, largura in (
        (end_ini, "#9ca3af", 3.0),
        (end_fim, "#2563eb", 6.0),
    ):
        sx, sy = w2s(ex, ez)
        partes.append(
            f'<line x1="{px_pivo:.1f}" y1="{py_pivo:.1f}" x2="{sx:.1f}" '
            f'y2="{sy:.1f}" stroke="{cor}" stroke-width="{largura}" '
            f'stroke-linecap="round"/>'
        )
        # Pega/manopla na extremidade.
        r_pega = max(diam_pega / 2 * escala, 5.0)
        partes.append(
            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r_pega:.1f}" '
            f'fill="#dc2626" stroke="#7f1d1d" stroke-width="1"/>'
        )

    # Eixo de pivô ----------------------------------------------------------
    partes.append(
        f'<circle cx="{px_pivo:.1f}" cy="{py_pivo:.1f}" r="6" '
        f'fill="#f59e0b" stroke="#78350f" stroke-width="1.5"/>'
    )

    # Legenda / cotas -------------------------------------------------------
    nome = _svg_escape(str(p["nome"]))
    linhas_texto = [
        f"{nome}",
        f"coluna: {altura_coluna:.0f} mm | alavanca: {comprimento:.0f} mm",
        f"pega Ø{diam_pega:.0f} mm | ADM: {ang_min:.0f}-{ang_max:.0f} graus",
    ]
    for i, linha in enumerate(linhas_texto):
        peso = "bold" if i == 0 else "normal"
        tam = 16 if i == 0 else 12
        partes.append(
            f'<text x="{margem:.0f}" y="{22 + i * 16}" font-family="sans-serif" '
            f'font-size="{tam}" font-weight="{peso}" fill="#111827">'
            f'{_svg_escape(linha)}</text>'
        )

    partes.append("</svg>")
    return "\n".join(partes)


# ==========================================================================
# Tool 8 — Render PNG via OpenSCAD CLI
# ==========================================================================
def renderizar_openscad_png(
    caminho_scad: str | Path,
    caminho_saida_png: str | Path | None = None,
    *,
    tamanho: tuple[int, int] = (1024, 768),
    camera: str | None = None,
    colorscheme: str = "Tomorrow",
    openscad_bin: str = "openscad",
    timeout_s: int = 120,
) -> str:
    """Renderiza um arquivo `.scad` em PNG usando o executável do OpenSCAD.

    Requer o OpenSCAD instalado no ambiente (``openscad`` no PATH, ou caminho
    informado em ``openscad_bin``). Não há fallback de render 3D em Python.

    Parameters
    ----------
    caminho_scad:
        Caminho do arquivo `.scad` de entrada.
    caminho_saida_png:
        Caminho do PNG de saída. Se omitido, usa o mesmo nome com `.png`.
    tamanho:
        ``(largura, altura)`` em pixels.
    camera:
        String de câmera do OpenSCAD (``--camera``). Se omitido, usa o
        enquadramento automático (``--viewall --autocenter``).
    colorscheme:
        Esquema de cores do render (``--colorscheme``).
    openscad_bin:
        Nome/caminho do executável do OpenSCAD.
    timeout_s:
        Tempo máximo do processo de render.

    Returns
    -------
    str
        Caminho do PNG gerado.

    Raises
    ------
    FileNotFoundError
        Se o `.scad` de entrada não existir.
    RuntimeError
        Se o executável do OpenSCAD não estiver disponível ou o render falhar.
    """
    caminho_scad = Path(caminho_scad)
    if not caminho_scad.is_file():
        raise FileNotFoundError(f"Arquivo .scad nao encontrado: {caminho_scad}")

    if shutil.which(openscad_bin) is None and not Path(openscad_bin).is_file():
        raise RuntimeError(
            f"Executavel do OpenSCAD nao encontrado ('{openscad_bin}'). "
            "Instale o OpenSCAD (https://openscad.org/downloads.html) ou "
            "informe o caminho via 'openscad_bin'. Para preview sem "
            "dependencias, use gerar_preview_svg()."
        )

    if caminho_saida_png is None:
        caminho_saida_png = caminho_scad.with_suffix(".png")
    caminho_saida_png = Path(caminho_saida_png)

    largura, altura = tamanho
    cmd: list[str] = [
        openscad_bin,
        "-o",
        str(caminho_saida_png),
        "--imgsize",
        f"{largura},{altura}",
        "--colorscheme",
        colorscheme,
    ]
    if camera:
        cmd += ["--camera", camera]
    else:
        cmd += ["--viewall", "--autocenter"]
    cmd.append(str(caminho_scad))

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s, check=False
        )
    except FileNotFoundError as exc:  # binário sumiu entre o which e o run
        raise RuntimeError(f"Falha ao invocar o OpenSCAD: {exc}") from exc

    if proc.returncode != 0 or not caminho_saida_png.is_file():
        raise RuntimeError(
            f"Render do OpenSCAD falhou (codigo {proc.returncode}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )

    return str(caminho_saida_png)


# ==========================================================================
# Tool 9 — Prompt para modelo de texto→imagem (render de produto)
# ==========================================================================
def montar_prompt_imagem_produto(
    parametros_geometria: dict[str, Any] | None = None,
    envelope_ergonomico: dict[str, Any] | None = None,
    *,
    estilo: str = "render de produto fotorrealista, fundo de estudio branco",
    idioma: str = "pt",
) -> dict[str, Any]:
    """Monta o *prompt* para gerar a imagem do produto em um modelo de imagem.

    Não chama nenhum provedor: retorna o *prompt* estruturado (positivo e
    negativo) para o agente orquestrador repassar à sua Tool de geração de
    imagem (texto→imagem), mantendo o núcleo provedor-agnóstico.

    Parameters
    ----------
    parametros_geometria:
        Dimensões/perfis da máquina (define o conteúdo descrito).
    envelope_ergonomico:
        Saída de ``projetar_ergonomia`` (opcional) para enriquecer o prompt
        com o tipo de exercício e a pegada.
    estilo:
        Direção de estilo visual do render.
    idioma:
        ``"pt"`` (padrão) ou ``"en"``.

    Returns
    -------
    dict
        ``{"prompt", "prompt_negativo", "parametros"}``.
    """
    p = _merge_parametros(parametros_geometria)

    descricao_ex = ""
    pegada_txt = ""
    if envelope_ergonomico:
        descricao_ex = envelope_ergonomico.get("nome", "")
        pegada = envelope_ergonomico.get("pegada", {}).get("orientacao", {})
        if pegada:
            pegada_txt = f", pegada {pegada.get('orientacao', '')}"

    if idioma == "en":
        prompt = (
            f"Photorealistic product render of an articulated gym strength "
            f"machine{(' - ' + descricao_ex) if descricao_ex else ''}. "
            f"Welded square steel tube (metalon) frame, upright column "
            f"~{p['altura_coluna_mm']:.0f} mm tall, pivoting lever arm "
            f"~{p['comprimento_alavanca_mm']:.0f} mm, padded seat and "
            f"ergonomic handle Ø~{p['diametro_pega_mm']:.0f} mm{pegada_txt}. "
            f"Industrial fitness equipment, matte black frame, three-quarter "
            f"view, {estilo}."
        )
        prompt_negativo = (
            "blurry, distorted proportions, floating parts, extra limbs, "
            "text, watermark, low quality, unrealistic joints"
        )
    else:
        prompt = (
            f"Render de produto fotorrealista de uma maquina de musculacao "
            f"articulada{(' - ' + descricao_ex) if descricao_ex else ''}. "
            f"Estrutura em tubo de aco quadrado (metalon) soldado, coluna "
            f"vertical de ~{p['altura_coluna_mm']:.0f} mm, braco articulado "
            f"de ~{p['comprimento_alavanca_mm']:.0f} mm, banco estofado e "
            f"pega ergonomica de Ø~{p['diametro_pega_mm']:.0f} mm{pegada_txt}. "
            f"Equipamento fitness profissional, estrutura preto fosco, vista "
            f"em tres-quartos, {estilo}."
        )
        prompt_negativo = (
            "borrado, proporcoes distorcidas, pecas flutuantes, membros "
            "extras, texto, marca d'agua, baixa qualidade, juntas irreais"
        )

    return {
        "prompt": prompt,
        "prompt_negativo": prompt_negativo,
        "parametros": {
            "altura_coluna_mm": p["altura_coluna_mm"],
            "comprimento_alavanca_mm": p["comprimento_alavanca_mm"],
            "diametro_pega_mm": p["diametro_pega_mm"],
            "estilo": estilo,
            "idioma": idioma,
        },
    }


# ==========================================================================
# Conveniência: grava o SVG em disco
# ==========================================================================
def gerar_imagem(
    parametros_geometria: dict[str, Any] | None,
    caminho_saida_svg: str | Path,
    **kwargs: Any,
) -> str:
    """Gera o preview SVG e grava em ``caminho_saida_svg``. Retorna o caminho."""
    svg = gerar_preview_svg(parametros_geometria, **kwargs)
    caminho = Path(caminho_saida_svg)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(svg, encoding="utf-8")
    return str(caminho)
