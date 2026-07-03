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
# Paleta (visual clássico Hammer Strength: estrutura platinada em tubo oval,
# estofados e anilhas pretos, pegas emborrachadas escuras)
# --------------------------------------------------------------------------
COR_ACO = "#a9aeb6"        # platinum (tubos principais)
COR_ACO_2 = "#8f959e"      # platinum sombreado (estrutura secundária)
COR_PAD = "#1c1e22"        # estofados pretos
COR_PEGA = "#3a3f46"       # pegas emborrachadas
COR_ANILHA = "#101214"
COR_ANILHA_ARO = "#2c3138"
COR_EIXO = "#d9a521"
COR_CAME = "#4c5560"

#: Cor do manequim de referência (posição do usuário).
COR_HUMANO = "#6f8cab"

#: Nomes das etapas de montagem, na ordem.
ETAPAS_MONTAGEM: list[str] = [
    "Chassi da base",
    "Estrutura dianteira do pivo",
    "Assento, apoio de peito e apoios de pes",
    "Eixos de pivo e cames",
    "Bracos articulados e pegas",
    "Suportes e anilhas",
    "Posicao do usuario (referencia)",
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


def _tubo(nome, etapa, cor, pontos, raio, explode, oval=1.0, lados=10,
          rot=None) -> dict[str, Any]:
    """Tubo varrido ao longo de uma polilinha 3D, com seção elíptica.

    Os pontos devem estar (aproximadamente) num plano X constante — caso
    típico dos membros do quadro; a seção usa o eixo lateral X como direção
    "larga" (``oval`` > 1 → tubo oval achatado, o visual Hammer Strength).
    A malha (vértices/faces) é pré-tesselada aqui, de modo que os
    renderizadores (Python e JS) só transformam e desenham.
    """
    pts = [list(map(float, q)) for q in pontos]
    n = len(pts)
    verts: list[list[float]] = []
    faces: list[list[int]] = []
    rx = raio * oval  # semieixo lateral (x)

    def _norm(v):
        m = math.sqrt(sum(c * c for c in v)) or 1.0
        return [c / m for c in v]

    for i, c in enumerate(pts):
        # Tangente média no nó (suaviza os cotovelos da polilinha).
        if i == 0:
            t = _norm([pts[1][k] - pts[0][k] for k in range(3)])
        elif i == n - 1:
            t = _norm([pts[-1][k] - pts[-2][k] for k in range(3)])
        else:
            a = _norm([pts[i][k] - pts[i - 1][k] for k in range(3)])
            b = _norm([pts[i + 1][k] - pts[i][k] for k in range(3)])
            t = _norm([a[k] + b[k] for k in range(3)])
        # Seção: eixo largo ~X (projetado ⊥ t), eixo estreito = t × u.
        u = [1.0 - t[0] * t[0], -t[0] * t[1], -t[0] * t[2]]
        u = _norm(u)
        v = _norm([t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2],
                   t[0] * u[1] - t[1] * u[0]])
        for k in range(lados):
            a = 2 * math.pi * k / lados
            ca, sa = math.cos(a), math.sin(a)
            verts.append([c[j] + rx * ca * u[j] + raio * sa * v[j] for j in range(3)])
    # Laterais
    for i in range(n - 1):
        for k in range(lados):
            k2 = (k + 1) % lados
            faces.append([i * lados + k, i * lados + k2,
                          (i + 1) * lados + k2, (i + 1) * lados + k])
    # Tampas
    faces.append(list(range(lados - 1, -1, -1)))
    faces.append(list(range((n - 1) * lados, n * lados)))

    p = {
        "nome": nome, "tipo": "mesh", "etapa": etapa, "cor": cor,
        "verts": [[round(c, 2) for c in vv] for vv in verts],
        "faces": faces, "explode": list(explode),
    }
    if rot:
        p["rot"] = rot
    return p


def gerar_pecas_maquina(
    parametros: dict[str, Any] | None = None,
    iso_lateral: bool = True,
    incluir_manequim: bool = True,
) -> dict[str, Any]:
    """Gera a lista de peças 3D da máquina a partir dos parâmetros do projeto.

    A arquitetura segue a Hammer Strength Iso-Lateral Row (IL-ROW,
    ~155×127×132 cm) e a cinemática da patente de Gary Jones ("a pair of
    levers pivotally connected to the frame in front of the brace and seat,
    each lever having a lower end adapted to support the weight and a
    handle at the upper end"):

    - o usuário senta **atrás**, peito no pad, pés nos apoios — acesso
      totalmente aberto ao banco;
    - cada lado tem uma **alavanca em C** de tubo oval: pivô **a meia
      altura à frente do peito**, pegas (neutra + pronada) na **ponta
      superior** junto ao tórax e chifre de anilhas na **ponta inferior**,
      baixa na frente da máquina (anilhas "tombadas" a ~45°);
    - puxar as pegas para trás gira a alavanca e levanta as anilhas — a
      came sintetizada no cubo modula o braço de momento;
    - visual clássico Hammer: tubos ovais platinados, estofados pretos.

    Parameters
    ----------
    parametros:
        Parâmetros de geometria do projeto: ``perfil_base_mm``,
        ``comprimento_alavanca_mm`` (distância pivô→pega),
        ``diametro_pega_mm``...
    iso_lateral:
        ``True`` (padrão): dois braços independentes espelhados.
    incluir_manequim:
        Adiciona a etapa final com um manequim sentado (referência de uso).

    Returns
    -------
    dict
        ``{"pecas": [...], "etapas": [...], "specs": {...}}``.

    Convenção: X = largura (0 no centro), Y = altura, Z = profundidade
    (0 = frente da máquina; o usuário senta em Z alto).
    """
    p = dict(parametros or {})
    perfil = float(p.get("perfil_base_mm", 60))
    alavanca = max(float(p.get("comprimento_alavanca_mm", 750)), 400.0)
    d_pega = float(p.get("diametro_pega_mm", 38))

    # Cotas de referência (Hammer IL-ROW: 1550 x 1270 x 1320 mm).
    # Cinemática conforme a patente de Gary Jones: "a pair of levers
    # pivotally connected to the frame IN FRONT of the brace and seat, each
    # lever having a LOWER end adapted to support the weight and a handle
    # at the UPPER end" — alavanca em C com pivô no meio, pegas em cima e
    # anilhas embaixo, na frente da máquina.
    prof = 1500.0
    pivo_y, pivo_z = 740.0, 330.0   # pivô a meia altura, à frente do peito
    assento_y = 420.0
    peito_z = 950.0                 # plano do apoio de peito

    # Direções da alavanca em C (ângulos a partir da vertical)
    a_sup = math.radians(42.0)      # ponta superior: para cima e para trás
    a_inf = math.radians(18.0)      # ponta inferior: para baixo e para frente
    r_inf = 470.0                   # raio do pivô à ponta inferior (pesos)
    topo_y = pivo_y + alavanca * math.cos(a_sup)
    topo_z = pivo_z + alavanca * math.sin(a_sup)
    base_lv_y = pivo_y - r_inf * math.cos(a_inf)
    base_lv_z = pivo_z - r_inf * math.sin(a_inf)

    pc: list[dict[str, Any]] = []

    def par(nome, fabrica):
        """Adiciona a peça espelhada em ±x (ou única no centro)."""
        if iso_lateral:
            fabrica(nome + " esq", -1)
            fabrica(nome + " dir", +1)
        else:
            fabrica(nome, 0)

    # ---- Etapa 1: chassi da base (tubos ovais platinados) ---------------
    e = 1
    pc.append(_tubo("Longarina central", e, COR_ACO, [(0, 46, -140), (0, 46, prof)], 40, (0, -1, 0), oval=1.5))
    pc.append(_tubo("Pe dianteiro", e, COR_ACO, [(-470, 42, 60), (470, 42, 60)], 34, (0, -1, -1), oval=1.0))
    pc.append(_tubo("Pe traseiro", e, COR_ACO, [(-400, 42, 1430), (400, 42, 1430)], 34, (0, -1, 1), oval=1.0))

    # ---- Etapa 2: estrutura dianteira do pivô ---------------------------
    e = 2
    pc.append(_tubo("Montante do pivo", e, COR_ACO, [(0, 60, 430), (0, 500, 395), (0, 720, 345)], 36, (0, 0, -1), oval=1.25))
    pc.append(_tubo("Escora frontal", e, COR_ACO_2, [(0, 60, 120), (0, 700, 328)], 26, (0, 0, -1)))
    pc.append(_tubo("Tirante traseiro", e, COR_ACO_2, [(0, 60, 950), (0, 712, 352)], 26, (0, 1, 1)))
    pc.append(_cilindro("Cubo do eixo", e, COR_ACO_2, (0, pivo_y, pivo_z), "x", 44, 620, (0, 1, -1), lados=16))

    # ---- Etapa 3: assento, apoio de peito e apoios de pés ---------------
    e = 3
    pc.append(_tubo("Coluna do apoio de peito", e, COR_ACO, [(0, 60, 1010), (0, 900, 962)], 34, (0, 1, 0), oval=1.25))
    pc.append(
        _caixa("Apoio de peito", e, COR_PAD, (-165, 810, peito_z - 45), (330, 300, 90), (0, 1, 0),
               rot={"eixo": "x", "graus": -8, "centro": [0, 960, peito_z]})
    )
    pc.append(_tubo("Coluna do assento", e, COR_ACO, [(0, 60, 1290), (0, assento_y, 1290)], 34, (0, 1, 1), oval=1.25))
    pc.append(_caixa("Banco estofado", e, COR_PAD, (-170, assento_y, 1120), (340, 65, 340), (0, 1, 1)))

    def _apoio_pe(nome, sx):
        pc.append(
            _caixa(nome, 3, COR_ACO_2, (sx * 180 - 100, 55, 730), (200, 22, 280), (sx, -1, 0),
                   rot={"eixo": "x", "graus": -38, "centro": [sx * 180, 66, 870]})
        )
    par("Apoio de pe", _apoio_pe)

    # ---- Etapa 4: eixos de pivô e cames ---------------------------------
    def _pivo(nome, sx):
        pc.append(_cilindro(nome, 4, COR_EIXO, (sx * 345, pivo_y, pivo_z), "x", 18, 90, (sx, 1, 0)))

    def _came(nome, sx):
        pc.append(_cilindro(nome, 4, COR_CAME, (sx * 245, pivo_y, pivo_z), "x", 88, 16, (sx, 1, 0), lados=18))

    par("Eixo de pivo", _pivo)
    par("Came", _came)

    # ---- Etapa 5: alavancas em C e pegas ---------------------------------
    bx_abs = 330.0
    du_y, du_z = math.cos(a_sup), math.sin(a_sup)          # direção p/ cima-trás
    perp_y, perp_z = -du_z, du_y                            # perpendicular (arqueia o C)

    def _alavanca_pts(bx):
        pts = [(bx, base_lv_y, base_lv_z), (bx, pivo_y - 210, pivo_z - 65), (bx, pivo_y, pivo_z)]
        for f, bow in ((0.45, 26.0), (0.78, 18.0), (1.0, 0.0)):
            pts.append((bx,
                        pivo_y + alavanca * f * du_y + bow * perp_y,
                        pivo_z + alavanca * f * du_z + bow * perp_z))
        return pts

    def _braco(nome, sx):
        bx = sx * bx_abs
        pc.append(_tubo(nome, 5, COR_ACO, _alavanca_pts(bx), 32, (sx, 1, 1), oval=1.2, lados=12))

    def _pega_h(nome, sx):
        # Travessa/pega pronada: da alavanca para dentro, na ponta superior.
        pc.append(_cilindro(nome, 5, COR_PEGA, (sx * (bx_abs - 105) + 0, topo_y, topo_z), "x",
                            d_pega / 2, 210, (sx, 1, 1)))

    def _pega_v(nome, sx):
        # Pega neutra vertical na extremidade interna da travessa.
        pc.append(_cilindro(nome, 5, COR_PEGA, (sx * 225, topo_y + 60, topo_z + 12), "y",
                            d_pega / 2, 300, (sx, 1, 1)))

    par("Braco articulado", _braco)
    par("Pega pronada", _pega_h)
    par("Pega neutra", _pega_v)

    pega_cy, pega_cz = topo_y + 60, topo_z + 12   # alvo do manequim

    # ---- Etapa 6: chifres de anilha (ponta inferior) e anilhas ----------
    a_ch = math.radians(42.0)   # chifre sobe para a frente a ~42°

    def _chifre(nome, sx):
        bx = sx * bx_abs
        fim_y = base_lv_y + 430 * math.cos(a_ch)
        fim_z = base_lv_z - 430 * math.sin(a_ch)
        pc.append(_tubo(nome, 6, COR_ACO_2, [(bx, base_lv_y, base_lv_z), (bx, fim_y, fim_z)], 24, (sx, 0, -1)))

    def _anilhas(nome, sx):
        bx = sx * bx_abs
        for k in range(3):
            t = 150 + 44 * k
            pc.append(
                _cilindro(f"{nome} #{k+1}", 6, COR_ANILHA if k % 2 == 0 else COR_ANILHA_ARO,
                          (bx, base_lv_y + t, base_lv_z), "y", 212, 36, (sx, 0, -1), lados=22,
                          rot={"eixo": "x", "graus": -math.degrees(a_ch) - 6,
                               "centro": [bx, base_lv_y, base_lv_z]})
            )

    par("Chifre de anilhas", _chifre)
    par("Anilha", _anilhas)

    # ---- Etapa 7: manequim (posição do usuário) --------------------------
    if incluir_manequim:
        e = 7
        topo_banco = assento_y + 65
        ombro_y, ombro_z = 1110, 1060
        pc.append(_caixa("Pelve (ref)", e, COR_HUMANO, (-150, topo_banco, 1150), (300, 180, 280), (0, 1, 1)))
        pc.append(
            _caixa("Tronco (ref)", e, COR_HUMANO, (-165, topo_banco + 155, peito_z + 50), (330, 470, 175), (0, 1, 1),
                   rot={"eixo": "x", "graus": 6, "centro": [0, topo_banco + 160, peito_z + 135]})
        )
        pc.append(_cilindro("Cabeca (ref)", e, COR_HUMANO, (0, 1250, 1075), "y", 85, 200, (0, 1, 1), lados=12))
        for sx in (-1, 1):
            lado = "esq" if sx < 0 else "dir"
            dy = pega_cy - ombro_y
            dz = pega_cz - ombro_z
            comp = math.hypot(dy, dz) + 30
            ang = -math.degrees(math.atan2(dz, -dy))
            pc.append(
                _caixa(f"Braco {lado} (ref)", e, COR_HUMANO, (sx * 200 - 35, ombro_y - comp, ombro_z - 35),
                       (70, comp, 70), (sx, 1, 1),
                       rot={"eixo": "x", "graus": ang, "centro": [sx * 200, ombro_y, ombro_z]})
            )
            pc.append(_caixa(f"Coxa {lado} (ref)", e, COR_HUMANO, (sx * 110 - 60, topo_banco + 10, 850), (120, 130, 400), (sx, 1, 1)))
            pc.append(
                _caixa(f"Canela {lado} (ref)", e, COR_HUMANO, (sx * 110 - 50, 110, 830), (100, topo_banco - 90, 100), (sx, 1, 1),
                       rot={"eixo": "x", "graus": -6, "centro": [sx * 110, topo_banco + 10, 880]})
            )

    specs = {
        "perfil_mm": perfil,
        "alavanca_mm": alavanca,
        "altura_pivo_mm": pivo_y,
        "diametro_pega_mm": d_pega,
        "iso_lateral": iso_lateral,
        "n_bracos": 2 if iso_lateral else 1,
        "base_mm": [1040, prof],
        "referencia": "layout Hammer Strength Iso-Lateral Row",
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
    if peca["tipo"] == "mesh":
        vs, fs = [list(v) for v in peca["verts"]], peca["faces"]
        rot = peca.get("rot")
        if rot:
            vs = [_rot_ponto(v, rot["eixo"], rot["graus"], rot["centro"]) for v in vs]
        return vs, fs
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
let yaw=1.05,pitch=0.22,zoom=1,giro=false,etapa=6,expl=0;
let drag=null;

function rot(v,e,g,c){const a=g*Math.PI/180,co=Math.cos(a),si=Math.sin(a);
 let x=v[0]-c[0],y=v[1]-c[1],z=v[2]-c[2];
 if(e==='x'){[y,z]=[y*co-z*si,y*si+z*co]}else if(e==='y'){[x,z]=[x*co+z*si,-x*si+z*co]}else{[x,y]=[x*co-y*si,x*si+y*co]}
 return[x+c[0],y+c[1],z+c[2]]}

function malha(q){let vs=[],fs=[];
 if(q.tipo==='mesh'){vs=q.verts.map(v=>v.slice());fs=q.faces;
  if(q.rot)vs=vs.map(v=>rot(v,q.rot.eixo,q.rot.graus,q.rot.centro));
  return[vs,fs]}
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
 const cx0=0,cy0=660,cz0=740; // centro aproximado do modelo
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
etapa=+rEt.value;
lista();specs();document.getElementById('oEt').textContent=etapa+'/'+D.etapas.length;draw();tick();
</script></body></html>""".replace("__TITULO__", titulo).replace("__DADOS__", dados)
