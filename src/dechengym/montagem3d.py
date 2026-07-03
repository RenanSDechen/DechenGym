"""
Módulo de Montagem 3D
=====================

Constrói um **modelo 3D paramétrico** da máquina (lista de peças com etapa
de montagem e direção de explosão) e o renderiza de duas formas:

- :func:`renderizar_svg_3d` — render estático sombreado (SVG), usado para
  gerar os PNGs do dossiê PDF em vários ângulos/etapas.
- :func:`gerar_visualizador_html` — **visualizador 3D interativo**
  auto-contido (HTML + Canvas 2D, zero dependências externas): arrastar
  para orbitar, roda para zoom, controle de etapa de montagem e de
  vista explodida.

O modelo é derivado das dimensões reais do projeto (perfil do metalon,
comprimento da alavanca, altura do pivô, diâmetro da pega) e suporta
máquinas **iso-laterais** (dois braços independentes) nativamente.

Convenção de eixos: X = largura (direita), Y = altura (cima),
Z = profundidade (fundo). Unidades em mm.
"""

from __future__ import annotations

import json
import math
from typing import Any

# --------------------------------------------------------------------------
# Paleta (acabamento premium: preto fosco, estofado vermelho, aço, latão)
# --------------------------------------------------------------------------
COR_ACO = "#23272e"
COR_ACO_2 = "#2e343d"
COR_PAD = "#b91c1c"
COR_PEGA = "#aab3bd"
COR_ANILHA = "#14161a"
COR_ANILHA_ARO = "#3a414b"
COR_EIXO = "#d9a521"
COR_CAME = "#4c5560"

#: Nomes das etapas de montagem, na ordem.
ETAPAS_MONTAGEM: list[str] = [
    "Chassi da base",
    "Torre traseira",
    "Assento e apoio de peito",
    "Eixos de pivo e cames",
    "Bracos articulados e pegas",
    "Suportes e anilhas",
]


# ==========================================================================
# Construção do modelo (lista de peças)
# ==========================================================================
def _caixa(nome, etapa, cor, pos, dim, explode, rot=None) -> dict[str, Any]:
    p = {
        "nome": nome, "tipo": "box", "etapa": etapa, "cor": cor,
        "pos": list(pos), "dim": list(dim), "explode": list(explode),
    }
    if rot:
        p["rot"] = rot  # {"eixo": "x"|"y"|"z", "graus": float, "centro": [x,y,z]}
    return p


def _cilindro(nome, etapa, cor, centro, eixo, raio, comprimento, explode,
              lados=14, rot=None) -> dict[str, Any]:
    p = {
        "nome": nome, "tipo": "cyl", "etapa": etapa, "cor": cor,
        "centro": list(centro), "eixo": eixo, "raio": raio,
        "comprimento": comprimento, "lados": lados, "explode": list(explode),
    }
    if rot:
        p["rot"] = rot
    return p


def gerar_pecas_maquina(
    parametros: dict[str, Any] | None = None,
    iso_lateral: bool = True,
) -> dict[str, Any]:
    """Gera a lista de peças 3D da máquina a partir dos parâmetros do projeto.

    Parameters
    ----------
    parametros:
        Parâmetros de geometria (as mesmas chaves de
        :func:`dechengym.gerar_script_openscad`): ``perfil_base_mm``,
        ``comprimento_alavanca_mm``, ``altura_coluna_mm``,
        ``diametro_pega_mm``, ``espessura_parede_mm``...
    iso_lateral:
        Se ``True`` (padrão), gera **dois braços independentes** espelhados
        com suportes de anilha (plate-loaded); senão, um braço central.

    Returns
    -------
    dict
        ``{"pecas": [...], "etapas": [...], "specs": {...}}``.
    """
    p = dict(parametros or {})
    perfil = float(p.get("perfil_base_mm", 60))
    alavanca = float(p.get("comprimento_alavanca_mm", 520))
    # Altura do eixo de pivô acima do piso (coluna + base).
    pivo_y = float(p.get("altura_coluna_mm", 540)) + perfil
    pivo_y = max(pivo_y, 750.0)  # sanidade visual p/ máquina sentada
    d_pega = float(p.get("diametro_pega_mm", 38))

    larg = 760.0        # largura total da base
    prof = 1150.0       # profundidade total da base
    torre_z = prof - 240
    torre_h = pivo_y + 260

    pc: list[dict[str, Any]] = []

    # ---- Etapa 1: chassi da base --------------------------------------
    e = 1
    pc.append(_caixa("Longarina esquerda", e, COR_ACO, (0, 0, 0), (perfil, perfil, prof), (0, -1, 0)))
    pc.append(_caixa("Longarina direita", e, COR_ACO, (larg - perfil, 0, 0), (perfil, perfil, prof), (0, -1, 0)))
    pc.append(_caixa("Travessa frontal", e, COR_ACO, (perfil, 0, 40), (larg - 2 * perfil, perfil, perfil), (0, -1, 0)))
    pc.append(_caixa("Travessa central", e, COR_ACO, (perfil, 0, prof * 0.48), (larg - 2 * perfil, perfil, perfil), (0, -1, 0)))
    pc.append(_caixa("Travessa traseira", e, COR_ACO, (perfil, 0, prof - perfil - 40), (larg - 2 * perfil, perfil, perfil), (0, -1, 0)))

    # ---- Etapa 2: torre traseira --------------------------------------
    e = 2
    for lado, x in (("esquerda", 120), ("direita", larg - 120 - perfil)):
        pc.append(_caixa(f"Coluna {lado}", e, COR_ACO_2, (x, perfil, torre_z), (perfil, torre_h - perfil, perfil), (0, 0, 1)))
    pc.append(_caixa("Travessa superior", e, COR_ACO_2, (120, torre_h, torre_z), (larg - 240, perfil, perfil), (0, 1, 1)))
    # Mãos-francesas
    for x in (120, larg - 120 - perfil):
        pc.append(_caixa("Reforco diagonal", e, COR_ACO_2, (x, perfil, torre_z - 150), (perfil, perfil, 150),
                         (0, 0, 1), rot={"eixo": "x", "graus": -35, "centro": [x, perfil + perfil / 2, torre_z]}))

    # ---- Etapa 3: assento + apoio de peito -----------------------------
    e = 3
    cx = larg / 2
    assento_y = 470.0
    pc.append(_caixa("Coluna do assento", e, COR_ACO, (cx - perfil / 2, perfil, 380), (perfil, assento_y - perfil, perfil), (0, 1, -1)))
    pc.append(_caixa("Banco estofado", e, COR_PAD, (cx - 150, assento_y, 300), (300, 60, 300), (0, 1, -1)))
    pc.append(_caixa("Haste do apoio de peito", e, COR_ACO, (cx - perfil / 2, assento_y + 60, 250), (perfil, pivo_y - assento_y - 50, perfil), (0, 1, -1)))
    pc.append(
        _caixa("Apoio de peito", e, COR_PAD, (cx - 170, pivo_y - 120, 200), (340, 280, 70), (0, 1, -1),
               rot={"eixo": "x", "graus": 12, "centro": [cx, pivo_y + 20, 235]})
    )

    # ---- Braços / pivôs / anilhas -------------------------------------
    if iso_lateral:
        bracos_x = [190.0, larg - 190.0]
    else:
        bracos_x = [cx]

    for i, bx in enumerate(bracos_x):
        lado = "esq" if (iso_lateral and i == 0) else ("dir" if iso_lateral else "central")
        esp_x = -1 if bx < cx else (1 if iso_lateral else 0)

        # Etapa 4: eixo de pivô + came
        e = 4
        pc.append(_cilindro(f"Eixo de pivo {lado}", e, COR_EIXO, (bx, pivo_y, torre_z + perfil / 2), "x", 16, 140, (esp_x, 0, 1)))
        pc.append(_cilindro(f"Came {lado}", e, COR_CAME, (bx + esp_x * 52, pivo_y, torre_z + perfil / 2), "x", 85, 16, (esp_x, 0, 1), lados=18))

        # Etapa 5: braço articulado + pega
        e = 5
        rot_braco = {"eixo": "x", "graus": 14, "centro": [bx, pivo_y, torre_z + perfil / 2]}
        pc.append(
            _caixa(f"Braco articulado {lado}", e, COR_ACO, (bx - perfil / 2, pivo_y - perfil / 2, torre_z + perfil / 2 - alavanca),
                   (perfil, perfil, alavanca), (esp_x, 0, -1), rot=rot_braco)
        )
        pc.append(
            _cilindro(f"Pega neutra {lado}", e, COR_PEGA, (bx, pivo_y - 185, torre_z + perfil / 2 - alavanca + 40),
                      "y", d_pega / 2, 370, (esp_x, 0, -1), rot=rot_braco)
        )

        # Etapa 6: suporte de anilhas (weight horn, atrás da torre) + anilhas
        e = 6
        horn_y = pivo_y - 320
        horn_z = torre_z + perfil + 60
        rot_horn = {"eixo": "x", "graus": 18, "centro": [bx, horn_y, horn_z]}
        pc.append(
            _cilindro(f"Suporte de anilhas {lado}", e, COR_ACO_2, (bx, horn_y, horn_z + 120), "z", 22, 280, (esp_x, 0, 1), rot=rot_horn)
        )
        for k in range(3):
            pc.append(
                _cilindro(f"Anilha {lado} #{k+1}", e, COR_ANILHA if k % 2 == 0 else COR_ANILHA_ARO,
                          (bx, horn_y, horn_z + 70 + k * 44), "z", 150, 32, (esp_x, 0, 1), lados=20, rot=rot_horn)
            )

    specs = {
        "perfil_mm": perfil,
        "alavanca_mm": alavanca,
        "altura_pivo_mm": round(pivo_y, 1),
        "diametro_pega_mm": d_pega,
        "iso_lateral": iso_lateral,
        "n_bracos": len(bracos_x),
        "base_mm": [larg, prof],
    }
    return {"pecas": pc, "etapas": ETAPAS_MONTAGEM, "specs": specs}


# ==========================================================================
# Renderizador 3D (Python) — para os PNGs do PDF
# ==========================================================================
def _rot_ponto(v, eixo, graus, centro):
    x, y, z = (v[0] - centro[0], v[1] - centro[1], v[2] - centro[2])
    a = math.radians(graus)
    c, s = math.cos(a), math.sin(a)
    if eixo == "x":
        y, z = y * c - z * s, y * s + z * c
    elif eixo == "y":
        x, z = x * c + z * s, -x * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return [x + centro[0], y + centro[1], z + centro[2]]


def _malha_peca(peca) -> tuple[list[list[float]], list[list[int]]]:
    """Vértices e faces (índices) de uma peça, já com rotação local aplicada."""
    if peca["tipo"] == "box":
        x, y, z = peca["pos"]
        w, h, d = peca["dim"]
        vs = [
            [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],
            [x, y, z + d], [x + w, y, z + d], [x + w, y + h, z + d], [x, y + h, z + d],
        ]
        fs = [
            [0, 1, 2, 3], [5, 4, 7, 6], [4, 0, 3, 7],
            [1, 5, 6, 2], [3, 2, 6, 7], [4, 5, 1, 0],
        ]
    else:  # cilindro
        cx, cy, cz = peca["centro"]
        eixo, r, comp, n = peca["eixo"], peca["raio"], peca["comprimento"], peca["lados"]
        vs, fs = [], []
        for extremo in (-comp / 2, comp / 2):
            for k in range(n):
                a = 2 * math.pi * k / n
                u, v = r * math.cos(a), r * math.sin(a)
                if eixo == "x":
                    vs.append([cx + extremo, cy + u, cz + v])
                elif eixo == "y":
                    vs.append([cx + u, cy + extremo, cz + v])
                else:
                    vs.append([cx + u, cy + v, cz + extremo])
        for k in range(n):
            k2 = (k + 1) % n
            fs.append([k, k2, n + k2, n + k])  # lateral
        fs.append(list(range(n - 1, -1, -1)))          # tampa 1
        fs.append(list(range(n, 2 * n)))               # tampa 2

    rot = peca.get("rot")
    if rot:
        vs = [_rot_ponto(v, rot["eixo"], rot["graus"], rot["centro"]) for v in vs]
    return vs, fs


def _shade(hexcol: str, f: float) -> str:
    h = hexcol.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


def renderizar_svg_3d(
    modelo: dict[str, Any],
    largura_px: int = 1000,
    yaw_graus: float = -32,
    pitch_graus: float = 16,
    etapa_max: int = 99,
    explosao: float = 0.0,
    titulo: str | None = None,
    subtitulo: str | None = None,
) -> str:
    """Renderiza o modelo em SVG sombreado (projeção ortográfica orbitável).

    ``etapa_max`` limita as peças mostradas (para ilustrar a sequência de
    montagem) e ``explosao`` (0–1) afasta os grupos na direção de explosão.
    """
    ya, pa = math.radians(yaw_graus), math.radians(pitch_graus)
    cy_, sy_ = math.cos(ya), math.sin(ya)
    cp, sp = math.cos(pa), math.sin(pa)
    luz = (0.45, 0.8, -0.4)
    lnorm = math.sqrt(sum(c * c for c in luz))
    luz = tuple(c / lnorm for c in luz)

    def cam(v):
        x, y, z = v
        x, z = x * cy_ + z * sy_, -x * sy_ + z * cy_       # yaw
        y, z = y * cp - z * sp, y * sp + z * cp            # pitch
        return x, y, z

    tris: list[tuple[float, str]] = []
    pecas = [q for q in modelo["pecas"] if q["etapa"] <= etapa_max]
    for q in pecas:
        vs, fs = _malha_peca(q)
        if explosao > 0:
            ex, ey, ez = q["explode"]
            off = 260.0 * explosao
            vs = [[v[0] + ex * off, v[1] + ey * off, v[2] + ez * off] for v in vs]
        pv = [cam(v) for v in vs]
        for f in fs:
            p0, p1, p2 = pv[f[0]], pv[f[1]], pv[f[2]]
            u = [p1[i] - p0[i] for i in range(3)]
            w = [p2[i] - p0[i] for i in range(3)]
            nx, ny, nz = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            if nz >= 0:  # backface (câmera olha -z)
                continue
            nn = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            dif = max(0.0, (nx * luz[0] + ny * luz[1] + nz * luz[2]) / nn)
            fator = 0.52 + 0.55 * dif
            cor = _shade(q["cor"], fator)
            zmed = sum(pv[i][2] for i in f) / len(f)
            pts = " ".join(f"{pv[i][0]:.1f},{-pv[i][1]:.1f}" for i in f)
            tris.append((zmed, f'<polygon points="{pts}" fill="{cor}" stroke="{_shade(q["cor"], 0.35)}" stroke-width="0.7" stroke-linejoin="round"/>'))

    tris.sort(key=lambda t: t[0])  # fundo -> frente

    # Bounding box em px
    import re as _re
    xs, ys2 = [], []
    for _, s in tris:
        for a, b in _re.findall(r"(-?\d+\.?\d*),(-?\d+\.?\d*)", s):
            xs.append(float(a)); ys2.append(float(b))
    if not xs:
        xs, ys2 = [0], [0]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys2), max(ys2)
    m = 70.0
    escala = (largura_px - 2 * m) / max(maxx - minx, 1)
    alt_px = int((maxy - miny) * escala + 2 * m + (70 if titulo else 0))
    ty_extra = 62 if titulo else 0

    corpo = "\n".join(s for _, s in tris)
    cab = ""
    if titulo:
        cab = (
            f'<text x="{m:.0f}" y="40" font-family="Helvetica, Arial, sans-serif" font-size="26" '
            f'font-weight="bold" fill="#161a20">{titulo}</text>'
        )
        if subtitulo:
            cab += (
                f'<text x="{m:.0f}" y="64" font-family="Helvetica, Arial, sans-serif" font-size="14" '
                f'fill="#5b6572">{subtitulo}</text>'
            )

    sombra_y = (maxy - miny) * escala + m + ty_extra + 6
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura_px}" height="{alt_px}" viewBox="0 0 {largura_px} {alt_px}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#f2f4f7"/><stop offset="1" stop-color="#dde2e9"/></linearGradient></defs>
<rect width="100%" height="100%" fill="url(#bg)"/>
<ellipse cx="{largura_px/2:.0f}" cy="{sombra_y:.0f}" rx="{(maxx-minx)*escala*0.46:.0f}" ry="26" fill="#000" opacity="0.13"/>
{cab}
<g transform="translate({m - minx * escala:.1f},{m + ty_extra - miny * escala:.1f}) scale({escala:.5f})">{corpo}</g>
</svg>'''


# ==========================================================================
# Visualizador 3D interativo (HTML auto-contido)
# ==========================================================================
def gerar_visualizador_html(
    modelo: dict[str, Any],
    titulo: str = "DechenGym — Montagem 3D",
    specs_extra: dict[str, Any] | None = None,
) -> str:
    """Gera o visualizador 3D interativo (HTML + Canvas, sem dependências).

    Controles: arrastar = orbitar · roda = zoom · slider de **etapa de
    montagem** (as peças aparecem na ordem de montagem) · slider de
    **vista explodida** · botão de rotação automática.
    """
    dados = json.dumps(
        {"pecas": modelo["pecas"], "etapas": modelo["etapas"],
         "specs": {**modelo["specs"], **(specs_extra or {})}},
        ensure_ascii=False,
    )
    # JS: mesmo pipeline do renderizador Python (rot local -> explode -> câmera
    # yaw/pitch -> cull -> sombreamento difuso -> painter sort).
    return """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__TITULO__</title>
<style>
:root{--bg:#0f1216;--panel:#171b21;--txt:#e8ebef;--mut:#9aa4b0;--acc:#e0a422}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--txt);font:14px/1.45 'Segoe UI',system-ui,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{padding:14px 20px;border-bottom:1px solid #262c34;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
header h1{font-size:18px}header span{color:var(--mut);font-size:12.5px}
main{flex:1;display:flex;min-height:0}
#c{flex:1 1 0;min-width:0;cursor:grab;touch-action:none}
aside{width:280px;flex:none;background:var(--panel);border-left:1px solid #262c34;padding:16px;overflow-y:auto}
aside h2{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);margin:14px 0 8px}
aside h2:first-child{margin-top:0}
.ctl{margin-bottom:10px}
.ctl label{display:flex;justify-content:space-between;font-size:12.5px;color:var(--mut);margin-bottom:4px}
.ctl output{color:var(--txt);font-weight:600}
input[type=range]{width:100%;accent-color:var(--acc)}
button{background:#232a33;border:1px solid #333c47;color:var(--txt);border-radius:8px;padding:7px 10px;font-size:12.5px;cursor:pointer;width:100%}
button.on{background:var(--acc);color:#14161a;border-color:var(--acc);font-weight:600}
ul{list-style:none}
li{display:flex;gap:8px;align-items:center;padding:4px 0;font-size:12.5px;color:var(--mut)}
li.atual{color:var(--txt);font-weight:600}
li i{width:18px;height:18px;border-radius:50%;background:#232a33;border:1px solid #333c47;display:inline-flex;align-items:center;justify-content:center;font-style:normal;font-size:10.5px;flex:none}
li.feita i{background:var(--acc);color:#14161a;border-color:var(--acc)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
td{padding:3px 0;color:var(--mut)}td+td{text-align:right;color:var(--txt)}
footer{padding:8px 20px;border-top:1px solid #262c34;color:var(--mut);font-size:11.5px}
</style></head><body>
<header><h1>__TITULO__</h1><span>arraste para orbitar &middot; roda do mouse = zoom</span></header>
<main>
<canvas id="c"></canvas>
<aside>
  <h2>Montagem</h2>
  <div class="ctl"><label>Etapa <output id="oEt">6/6</output></label>
    <input id="rEt" type="range" min="1" max="6" step="1" value="6"></div>
  <ul id="lista"></ul>
  <h2>Vista</h2>
  <div class="ctl"><label>Explos&atilde;o <output id="oEx">0%</output></label>
    <input id="rEx" type="range" min="0" max="100" step="1" value="0"></div>
  <div class="ctl"><button id="bGiro">&#8635; Rota&ccedil;&atilde;o autom&aacute;tica</button></div>
  <h2>Especifica&ccedil;&otilde;es</h2>
  <table id="specs"></table>
</aside>
</main>
<footer>DechenGym &middot; visualizador de montagem gerado automaticamente a partir do projeto param&eacute;trico</footer>
<script>
const D=__DADOS__;
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
let yaw=-0.56,pitch=0.30,zoom=1,giro=false,etapa=6,expl=0;
let drag=null;

function rot(v,e,g,c){const a=g*Math.PI/180,co=Math.cos(a),si=Math.sin(a);
 let x=v[0]-c[0],y=v[1]-c[1],z=v[2]-c[2];
 if(e==='x'){[y,z]=[y*co-z*si,y*si+z*co]}else if(e==='y'){[x,z]=[x*co+z*si,-x*si+z*co]}else{[x,y]=[x*co-y*si,x*si+y*co]}
 return[x+c[0],y+c[1],z+c[2]]}

function malha(q){let vs=[],fs=[];
 if(q.tipo==='box'){const[x,y,z]=q.pos,[w,h,d]=q.dim;
  vs=[[x,y,z],[x+w,y,z],[x+w,y+h,z],[x,y+h,z],[x,y,z+d],[x+w,y,z+d],[x+w,y+h,z+d],[x,y+h,z+d]];
  fs=[[0,1,2,3],[5,4,7,6],[4,0,3,7],[1,5,6,2],[3,2,6,7],[4,5,1,0]];}
 else{const[cx,cy,cz]=q.centro,n=q.lados,r=q.raio,L=q.comprimento;
  for(const ex of[-L/2,L/2])for(let k=0;k<n;k++){const a=2*Math.PI*k/n,u=r*Math.cos(a),v=r*Math.sin(a);
   if(q.eixo==='x')vs.push([cx+ex,cy+u,cz+v]);else if(q.eixo==='y')vs.push([cx+u,cy+ex,cz+v]);else vs.push([cx+u,cy+v,cz+ex]);}
  for(let k=0;k<n;k++){const k2=(k+1)%n;fs.push([k,k2,n+k2,n+k])}
  fs.push(Array.from({length:n},(_,i)=>n-1-i));fs.push(Array.from({length:n},(_,i)=>n+i));}
 if(q.rot)vs=vs.map(v=>rot(v,q.rot.eixo,q.rot.graus,q.rot.centro));
 return[vs,fs]}

function shade(hex,f){const h=hex.slice(1),r=parseInt(h.slice(0,2),16),g=parseInt(h.slice(2,4),16),b=parseInt(h.slice(4,6),16);
 const m=x=>Math.max(0,Math.min(255,Math.round(x*f)));return`rgb(${m(r)},${m(g)},${m(b)})`}

function draw(){
 const W=cv.clientWidth,H=cv.clientHeight;
 if(cv.width!==W*devicePixelRatio){cv.width=W*devicePixelRatio;cv.height=H*devicePixelRatio}
 ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
 const g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#12161c');g.addColorStop(1,'#0a0d11');
 ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
 const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const luz=[0.45,0.8,-0.4],ln=Math.hypot(...luz),lz=luz.map(c=>c/ln);
 const cx0=380,cy0=650,cz0=575; // centro aproximado do modelo
 const tris=[];
 for(const q of D.pecas){
  if(q.etapa>etapa)continue;
  let[vs,fs]=malha(q);
  if(expl>0){const off=260*expl;vs=vs.map(v=>[v[0]+q.explode[0]*off,v[1]+q.explode[1]*off,v[2]+q.explode[2]*off])}
  const pv=vs.map(v=>{let x=v[0]-cx0,y=v[1]-cy0,z=v[2]-cz0;
   [x,z]=[x*cy+z*sy,-x*sy+z*cy];[y,z]=[y*cp-z*sp,y*sp+z*cp];return[x,y,z]});
  for(const f of fs){const p0=pv[f[0]],p1=pv[f[1]],p2=pv[f[2]];
   const ux=p1[0]-p0[0],uy=p1[1]-p0[1],uz=p1[2]-p0[2],wx=p2[0]-p0[0],wy=p2[1]-p0[1],wz=p2[2]-p0[2];
   const nx=uy*wz-uz*wy,ny=uz*wx-ux*wz,nz2=ux*wy-uy*wx;
   if(nz2>=0)continue;
   const nn=Math.hypot(nx,ny,nz2)||1,dif=Math.max(0,(nx*lz[0]+ny*lz[1]+nz2*lz[2])/nn);
   const zm=(p0[2]+p1[2]+p2[2])/3;
   tris.push([zm,f.map(i=>pv[i]),shade(q.cor,0.52+0.55*dif)])}}
 tris.sort((a,b)=>a[0]-b[0]);
 const s=Math.min(W,H)/2100*zoom;
 ctx.save();ctx.translate(W/2,H/2+30);
 for(const[,pts,cor]of tris){ctx.beginPath();
  ctx.moveTo(pts[0][0]*s,-pts[0][1]*s);
  for(let i=1;i<pts.length;i++)ctx.lineTo(pts[i][0]*s,-pts[i][1]*s);
  ctx.closePath();ctx.fillStyle=cor;ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,.45)';ctx.lineWidth=.6;ctx.stroke()}
 ctx.restore()}

function tick(){if(giro){yaw+=0.006;draw()}requestAnimationFrame(tick)}

cv.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];cv.setPointerCapture(e.pointerId);cv.style.cursor='grabbing'});
cv.addEventListener('pointermove',e=>{if(!drag)return;
 yaw+=(e.clientX-drag[0])*0.008;pitch=Math.max(-1.3,Math.min(1.3,pitch+(e.clientY-drag[1])*0.008));
 drag=[e.clientX,e.clientY];draw()});
cv.addEventListener('pointerup',()=>{drag=null;cv.style.cursor='grab'});
cv.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.35,Math.min(4,zoom*(e.deltaY<0?1.1:0.9)));draw()},{passive:false});

const rEt=document.getElementById('rEt'),rEx=document.getElementById('rEx');
rEt.max=D.etapas.length;rEt.value=D.etapas.length;
rEt.oninput=()=>{etapa=+rEt.value;document.getElementById('oEt').textContent=etapa+'/'+D.etapas.length;lista();draw()};
rEx.oninput=()=>{expl=rEx.value/100;document.getElementById('oEx').textContent=rEx.value+'%';draw()};
document.getElementById('bGiro').onclick=e=>{giro=!giro;e.target.classList.toggle('on',giro)};

function lista(){document.getElementById('lista').innerHTML=D.etapas.map((n,i)=>
 `<li class="${i+1<etapa?'feita':''} ${i+1===etapa?'atual':''}"><i>${i+1}</i>${n}</li>`).join('')}
function specs(){const s=D.specs,fmt=[['Tipo',s.iso_lateral?'Iso-lateral (2 bracos)':'Braco unico'],
 ['Perfil','Metalon '+s.perfil_mm+'x'+s.perfil_mm+' mm'],['Alavanca',s.alavanca_mm+' mm'],
 ['Altura do pivo',s.altura_pivo_mm+' mm'],['Pega','&Oslash; '+s.diametro_pega_mm+' mm'],
 ['Base',s.base_mm[0]+' x '+s.base_mm[1]+' mm']];
 for(const k in s){if(['perfil_mm','alavanca_mm','altura_pivo_mm','diametro_pega_mm','iso_lateral','n_bracos','base_mm'].includes(k))continue;
  fmt.push([k.replaceAll('_',' '),s[k]])}
 document.getElementById('specs').innerHTML=fmt.map(([a,b])=>`<tr><td>${a}</td><td>${b}</td></tr>`).join('')}
new ResizeObserver(draw).observe(cv);
lista();specs();document.getElementById('oEt').textContent=etapa+'/'+D.etapas.length;draw();tick();
</script></body></html>""".replace("__TITULO__", titulo).replace("__DADOS__", dados)
