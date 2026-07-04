"""
Módulo de Dossiê PDF
====================

Gera o **dossiê técnico em PDF** de um projeto (saída de
:func:`dechengym.orquestrador.projetar_maquina`): capa com render 3D,
ergonomia, came (curva de força × resistência), estrutura com o histórico de
autocorreção, memorial de cortes e o **passo a passo de montagem** com um
render 3D por etapa.

Dependências: ``reportlab`` (composição) e ``cairosvg`` (rasterização dos
renders SVG 3D). Ambas puras-Python/instaláveis via pip.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from dechengym.montagem3d import (
    ETAPAS_MONTAGEM,
    gerar_pecas_maquina,
    renderizar_svg_3d,
)

# Paleta do documento
_INK = "#161a20"
_MUT = "#5b6572"
_ACC = "#b91c1c"
_OK = "#15803d"
_LINHA = "#d7dce3"
_FUNDO_TAB = "#f2f4f7"


def _cor(hexcol):
    from reportlab.lib.colors import HexColor

    return HexColor(hexcol)


def _png_do_svg(svg: str, largura_px: int) -> "io.BytesIO":
    import cairosvg

    buf = io.BytesIO()
    cairosvg.svg2png(bytestring=svg.encode(), write_to=buf, output_width=largura_px)
    buf.seek(0)
    return buf


class _Doc:
    """Helper de layout: cabeçalho/rodapé, seções, tabelas e imagens."""

    def __init__(self, caminho: str, titulo: str):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        self.W, self.H = A4
        self.c = canvas.Canvas(caminho, pagesize=A4)
        self.titulo = titulo
        self.m = 46.0
        self.y = self.H - self.m
        self.pagina = 0
        self._nova_pagina_interna(primeira=True)

    # -- páginas ---------------------------------------------------------
    def _nova_pagina_interna(self, primeira=False):
        if not primeira:
            self._rodape()
            self.c.showPage()
        self.pagina += 1
        self.y = self.H - self.m
        if not primeira and self.pagina > 1:
            self._cabecalho()

    def _cabecalho(self):
        c = self.c
        c.setFillColor(_cor(_MUT))
        c.setFont("Helvetica", 8)
        c.drawString(self.m, self.H - 24, "DECHENGYM · DOSSIÊ TÉCNICO")
        c.drawRightString(self.W - self.m, self.H - 24, self.titulo)
        c.setStrokeColor(_cor(_LINHA))
        c.setLineWidth(0.7)
        c.line(self.m, self.H - 30, self.W - self.m, self.H - 30)
        self.y = self.H - 52

    def _rodape(self):
        c = self.c
        c.setStrokeColor(_cor(_LINHA))
        c.setLineWidth(0.7)
        c.line(self.m, 34, self.W - self.m, 34)
        c.setFillColor(_cor(_MUT))
        c.setFont("Helvetica", 8)
        c.drawString(self.m, 22, "Gerado automaticamente pelo pipeline DechenGym")
        c.drawRightString(self.W - self.m, 22, f"pág. {self.pagina}")

    def precisa(self, altura: float):
        if self.y - altura < 60:
            self._nova_pagina_interna()

    # -- blocos ----------------------------------------------------------
    def secao(self, num: str, nome: str):
        self.precisa(46)
        c = self.c
        c.setFillColor(_cor(_ACC))
        c.rect(self.m, self.y - 15, 3.2, 17, stroke=0, fill=1)
        c.setFillColor(_cor(_INK))
        c.setFont("Helvetica-Bold", 14.5)
        c.drawString(self.m + 11, self.y - 12, f"{num}  {nome}")
        self.y -= 32

    def paragrafo(self, texto: str, tam=9.5, cor=_MUT, entrelinha=13.0, largura=None):
        from reportlab.pdfbase.pdfmetrics import stringWidth

        larg = largura or (self.W - 2 * self.m)
        palavras = texto.split()
        linhas, atual = [], ""
        for p in palavras:
            t = (atual + " " + p).strip()
            if stringWidth(t, "Helvetica", tam) <= larg:
                atual = t
            else:
                linhas.append(atual)
                atual = p
        if atual:
            linhas.append(atual)
        self.precisa(len(linhas) * entrelinha + 6)
        self.c.setFont("Helvetica", tam)
        self.c.setFillColor(_cor(cor))
        for ln in linhas:
            self.c.drawString(self.m, self.y - tam, ln)
            self.y -= entrelinha
        self.y -= 4

    def tabela(self, linhas: list[list[str]], colunas: list[float],
               cab: bool = True, alinh: list[str] | None = None, tam=9.0):
        alt = 16.0
        self.precisa(alt * len(linhas) + 8)
        c = self.c
        x0 = self.m
        for i, linha in enumerate(linhas):
            y0 = self.y - alt
            if i == 0 and cab:
                c.setFillColor(_cor(_INK))
                c.rect(x0, y0, sum(colunas), alt, stroke=0, fill=1)
                c.setFillColor(_cor("#ffffff"))
                c.setFont("Helvetica-Bold", tam - 0.5)
            else:
                if i % 2 == (0 if not cab else 0):
                    c.setFillColor(_cor(_FUNDO_TAB))
                    c.rect(x0, y0, sum(colunas), alt, stroke=0, fill=1)
                c.setFillColor(_cor(_INK))
                c.setFont("Helvetica", tam)
            x = x0
            for j, cel in enumerate(linha):
                a = (alinh or ["e"] * len(colunas))[j]
                tx = str(cel)
                if a == "d":
                    c.drawRightString(x + colunas[j] - 6, y0 + 4.5, tx)
                else:
                    c.drawString(x + 6, y0 + 4.5, tx)
                x += colunas[j]
            self.y -= alt
        c.setStrokeColor(_cor(_LINHA))
        c.setLineWidth(0.6)
        c.rect(x0, self.y, sum(colunas), alt * len(linhas), stroke=1, fill=0)
        self.y -= 10

    def imagem(self, png_buf: "io.BytesIO", largura: float, altura: float,
               centrado=True, borda=False):
        from reportlab.lib.utils import ImageReader

        self.precisa(altura + 8)
        img = ImageReader(png_buf)
        iw, ih = img.getSize()
        # Ajusta o quadro à proporção real da imagem (evita imagem deslocada).
        prop = ih / iw
        if largura * prop > altura:
            largura = altura / prop
        else:
            altura = largura * prop
        x = (self.W - largura) / 2 if centrado else self.m
        self.c.drawImage(img, x, self.y - altura, width=largura, height=altura, mask="auto")
        if borda:
            self.c.setStrokeColor(_cor(_LINHA))
            self.c.rect(x, self.y - altura, largura, altura, stroke=1, fill=0)
        self.y -= altura + 8


def _grafico_curvas(avaliacao: dict[str, Any], largura: float, altura: float):
    """Desenha (em memória, via SVG) o gráfico força humana × resistência da came."""
    pcts = avaliacao["amostras_pct"]
    hn = avaliacao["perfil_humano_norm"]
    mn = avaliacao["perfil_maquina_norm"]
    W, H = 640, 300
    mx, my = 56, 40
    gw, gh = W - mx - 24, H - 2 * my

    def px(p):
        return mx + gw * (p / 100.0)

    def py(v):
        return H - my - gh * ((v - 0.4) / 0.65)

    grade = "".join(
        f'<line x1="{px(p)}" y1="{H-my}" x2="{px(p)}" y2="{my}" stroke="#e3e7ec" stroke-width="1"/>'
        f'<text x="{px(p)}" y="{H-my+16}" font-size="11" text-anchor="middle" fill="#5b6572" font-family="Helvetica">{p}%</text>'
        for p in pcts
    )
    eixo_y = "".join(
        f'<line x1="{mx}" y1="{py(v)}" x2="{W-24}" y2="{py(v)}" stroke="#eef1f5" stroke-width="1"/>'
        f'<text x="{mx-8}" y="{py(v)+4}" font-size="11" text-anchor="end" fill="#5b6572" font-family="Helvetica">{v:.1f}</text>'
        for v in (0.5, 0.7, 0.9, 1.0)
    )

    def linha(vals, cor, tracejada=False):
        pts = " ".join(f"{px(p):.1f},{py(v):.1f}" for p, v in zip(pcts, vals))
        dash = 'stroke-dasharray="7 5"' if tracejada else ""
        circ = "".join(
            f'<circle cx="{px(p):.1f}" cy="{py(v):.1f}" r="4" fill="{cor}"/>'
            for p, v in zip(pcts, vals)
        )
        return f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="2.6" {dash}/>' + circ

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="100%" height="100%" fill="#ffffff"/>
{grade}{eixo_y}
<line x1="{mx}" y1="{H-my}" x2="{W-24}" y2="{H-my}" stroke="#9aa4b0" stroke-width="1.4"/>
{linha(hn, "#b91c1c")}
{linha(mn, "#1d4ed8", tracejada=True)}
<rect x="{mx}" y="10" width="14" height="4" fill="#b91c1c"/>
<text x="{mx+20}" y="16" font-size="12" fill="#161a20" font-family="Helvetica">Curva de forca humana (normalizada)</text>
<rect x="{mx+250}" y="10" width="14" height="4" fill="#1d4ed8"/>
<text x="{mx+270}" y="16" font-size="12" fill="#161a20" font-family="Helvetica">Resistencia da came sintetizada</text>
</svg>'''
    return _png_do_svg(svg, 1000)


def gerar_dossie_pdf(
    projeto: dict[str, Any],
    caminho_pdf: str | Path,
    titulo: str | None = None,
    iso_lateral: bool = True,
) -> str:
    """Gera o dossiê técnico completo em PDF. Retorna o caminho gravado.

    Parameters
    ----------
    projeto:
        Saída de :func:`dechengym.orquestrador.projetar_maquina`.
    caminho_pdf:
        Arquivo de destino (``.pdf``).
    titulo:
        Título comercial do equipamento (padrão: nome do exercício).
    iso_lateral:
        Se o modelo 3D deve ter dois braços independentes.
    """
    caminho_pdf = str(caminho_pdf)
    req = projeto["requisicao"]
    erg = projeto["ergonomia"]
    came = projeto["came"]
    estr = projeto["estrutura"]
    mem = projeto["geometria"]["memorial"]
    titulo = titulo or erg["nome"]

    modelo = gerar_pecas_maquina(projeto["geometria"]["parametros"], iso_lateral=iso_lateral)
    doc = _Doc(caminho_pdf, titulo)
    c = doc.c

    # ================= CAPA =================
    c.setFillColor(_cor(_INK))
    c.rect(0, doc.H - 150, doc.W, 150, stroke=0, fill=1)
    c.setFillColor(_cor(_ACC))
    c.rect(0, doc.H - 150, 8, 150, stroke=0, fill=1)
    c.setFillColor(_cor("#ffffff"))
    c.setFont("Helvetica-Bold", 25)
    c.drawString(doc.m, doc.H - 74, titulo)
    c.setFont("Helvetica", 11.5)
    c.setFillColor(_cor("#b9c1cb"))
    c.drawString(doc.m, doc.H - 96, "Dossiê técnico de projeto — ergonomia · came · estrutura · montagem")
    c.setFont("Helvetica", 9.5)
    c.drawString(doc.m, doc.H - 128,
                 f"Carga de projeto {req['carga_kg']:.0f} kg  ·  perfil {req['perfil']}  ·  "
                 f"fator de segurança {req['fator_seguranca']}  ·  público P5–P95")
    aprovado = projeto["aprovado"]
    c.setFillColor(_cor(_OK if aprovado else _ACC))
    c.roundRect(doc.W - doc.m - 120, doc.H - 100, 120, 30, 6, stroke=0, fill=1)
    c.setFillColor(_cor("#ffffff"))
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(doc.W - doc.m - 60, doc.H - 90, "APROVADO" if aprovado else "REVISAR")
    doc.y = doc.H - 175

    hero = renderizar_svg_3d(modelo, largura_px=1100, yaw_graus=62, pitch_graus=10)
    doc.imagem(_png_do_svg(hero, 1500), doc.W - 2 * doc.m, 385)
    doc.paragrafo(projeto["resumo"] + " Arquitetura de referencia: maquinas "
                  "plate-loaded iso-laterais topo de linha (pivo alto no mastro "
                  "dianteiro, assento traseiro aberto, anilhas nos chifres "
                  "frontais). O manequim ilustra a posicao de uso.", tam=10, cor=_INK)

    # ================= 1. ERGONOMIA =================
    doc._nova_pagina_interna()
    doc.secao("1", "Ergonomia e biomecânica")
    peg = erg["pegada"]
    adm = erg["amplitude_movimento"]
    aj = erg["ajustes_posto"]["altura_assento"]
    doc.tabela(
        [
            ["Parâmetro", "Valor", "Referência"],
            ["Articulação / movimento", f"{erg['articulacao']} / {erg['movimento']}", "catálogo de exercícios"],
            ["Grupo muscular", erg["grupo_muscular"], f"curva {came['perfil']['tipo_curva']}"],
            ["Altura do eixo de pivô", f"{erg['alinhamento_pivo']['altura_pivo_mm']} mm", erg["alinhamento_pivo"]["medida_referencia"]],
            ["ADM de treino", f"{adm['adm_treino'][0]}° – {adm['adm_treino'][1]}°", f"anatômica {adm['adm_anatomica'][0]}°–{adm['adm_anatomica'][1]}°"],
            ["Orientação da pegada", peg["orientacao"]["orientacao"], peg["orientacao"]["enfase"][:46]],
            ["Diâmetro da pega", f"Ø {peg['diametro']['diametro_recomendado_mm']} mm", f"~20% do compr. da mão ({peg['diametro']['comprimento_mao_mm']} mm)"],
            ["Distância entre pegas", f"{peg['largura']['distancia_entre_pegas_mm']} mm", f"{peg['largura']['largura']} (biacromial)"],
            ["Regulagem do assento", f"{aj['minimo_mm']} – {aj['maximo_mm']} mm", f"curso {aj['curso_mm']} mm (P5 fem – P95 masc)"],
        ],
        [150, 130, 223],
    )
    doc.paragrafo(
        "O eixo mecânico de rotação coincide com o eixo anatômico da articulação "
        "trabalhada — critério ergonômico central de uma máquina articulada. As "
        "regulagens cobrem o envelope antropométrico da mulher P5 ao homem P95."
    )

    # ================= 2. CAME =================
    doc.secao("2", "Came de resistência variável")
    av = came["avaliacao"]
    doc.paragrafo(
        f"O raio efetivo da came é proporcional à curva de força do grupo "
        f"muscular ({erg['grupo_muscular']}, perfil {came['perfil']['tipo_curva']}): "
        f"r(θ) = r_max × S_norm(θ). Raio {came['perfil']['raio_min_mm']}–"
        f"{came['perfil']['raio_max_mm']} mm ao longo de "
        f"{came['perfil']['amplitude_graus']:.0f}° de rotação.",
        cor=_INK,
    )
    doc.imagem(_grafico_curvas(av, doc.W - 2 * doc.m - 60, 240), doc.W - 2 * doc.m - 60, 240, borda=True)
    doc.tabela(
        [
            ["% do movimento"] + [f"{p}%" for p in av["amostras_pct"]],
            ["Torque da came (N·m)"] + [f"{t:.1f}" for t in came["resistencia"]["torque_nm"]],
        ],
        [150] + [70.6] * 5,
        alinh=["e", "d", "d", "d", "d", "d"],
    )
    doc.paragrafo(
        f"Prova por round-trip: a resistência recalculada da came, reavaliada contra a "
        f"curva de força, pontua {av['pontuacao']}/100 — {av['recomendacao']}",
        cor=_OK if av["pontuacao"] >= 90 else _ACC,
    )

    # ================= 3. ESTRUTURA =================
    doc._nova_pagina_interna()
    doc.secao("3", "Validação estrutural com autocorreção")
    rel = estr["relatorio"]
    doc.paragrafo(
        f"Momento fletor de projeto: {rel['momento_fletor_nm']} N·m "
        f"({req['carga_kg']:.0f} kg em alavanca de {req['comprimento_alavanca_mm']:.0f} mm). "
        f"Critério: tensão de flexão ≤ escoamento / FS (FS = {req['fator_seguranca']}). "
        f"O laço de autocorreção itera as espessuras comerciais do perfil {req['perfil']} "
        f"até a aprovação:",
        cor=_INK,
    )
    linhas = [["Iteração", "Parede (mm)", "Utilização σ/σ_adm", "Resultado"]]
    for i, it in enumerate(estr["iteracoes"], 1):
        linhas.append([
            str(i), f"{it['espessura_parede_mm']}", f"{it['coef_utilizacao']:.3f}",
            "APROVADO" if it["aprovado"] else "reprovado",
        ])
    doc.tabela(linhas, [90, 120, 160, 133], alinh=["e", "d", "d", "e"])
    doc.tabela(
        [
            ["Grandeza", "Valor"],
            ["Espessura selecionada", f"{estr['espessura_escolhida_mm']} mm"],
            ["Tensão de flexão", f"{rel['tensao_flexao_mpa']} MPa"],
            ["Tensão admissível", f"{rel['tensao_admissivel_mpa']} MPa"],
            ["Coeficiente de utilização", f"{rel['coef_utilizacao']:.3f}"],
        ],
        [220, 283],
    )

    # ================= 4. MEMORIAL =================
    doc.secao("4", "Memorial de cortes e materiais")
    fator = 2 if iso_lateral else 1
    linhas = [["Peça", "Perfil", "Corte (mm)", "Qtd", "Massa (kg)"]]
    total = 0.0
    for p in mem["lista_cortes"]:
        qtd = p["quantidade"] * fator
        massa = (p["peso_total_kg"] or 0) * fator
        total += massa
        linhas.append([p["descricao"], f"{p['perfil']} ×{p['espessura_parede_mm']}", f"{p['comprimento_corte_mm']:.0f}", str(qtd), f"{massa:.2f}"])
    linhas.append(["TOTAL (estrutura)", "", "", "", f"{total:.2f}"])
    doc.tabela(linhas, [178, 105, 80, 50, 90], alinh=["e", "e", "d", "d", "d"])
    if iso_lateral:
        doc.paragrafo("Quantidades e massas já consideram os DOIS braços independentes (iso-lateral).")
    for aviso in mem.get("avisos", []):
        doc.paragrafo("⚠ " + aviso, cor=_ACC)

    # ================= 5. FABRICAÇÃO INDUSTRIAL =================
    doc._nova_pagina_interna()
    doc.secao("5", "Plano de fabricação industrial")
    fab = projeto.get("fabricacao")
    if fab:
        est = fab["estrutura"]
        doc.paragrafo(
            f"Perfil principal: {est['perfil_principal']} — {est['observacao_perfil']} "
            f"Footprint {est['footprint_mm'][0]} x {est['footprint_mm'][1]} mm; altura máxima "
            f"das hastes {est['altura_maxima_hastes_mm']} mm. {est['base']}.",
            cor=_INK,
        )
        linhas = [["Componente", "Material / processo", "Esp. (mm)", "Qtd"]]
        for c_ in fab["componentes"]:
            esp = f"{c_['espessura_mm']}" if c_["espessura_mm"] else "—"
            linhas.append([c_["item"], f"{c_['material']} · {c_['processo']}"[:58], esp, str(c_["quantidade"])])
        doc.tabela(linhas, [150, 253, 55, 45], alinh=["e", "e", "d", "d"], tam=8.0)
        linhas = [["Processo", "Aplicação"]]
        for pr in fab["processos"]:
            linhas.append([pr["processo"], f"{pr['aplicacao']} — {pr['justificativa']}"[:74]])
        doc.tabela(linhas, [170, 333], tam=8.0)
        ac = fab["acabamento"]
        doc.paragrafo(
            f"Acabamento: {ac['preparacao']}. Pintura: {ac['pintura']}. Estofados: {ac['estofados']}."
        )

    # ================= 6. MONTAGEM =================
    doc._nova_pagina_interna()
    doc.secao("6", "Sequência de montagem")
    doc.paragrafo(
        "Renders gerados do modelo 3D paramétrico. A versão interativa "
        "(orbitar, explodir, avançar etapas) acompanha este dossiê no arquivo "
        "montagem_3d.html.",
    )
    inst = [
        "Nivele a longarina central e solde os pés dianteiro e traseiro.",
        "Levante o pilar dianteiro do pivô, a travessa do eixo e as escoras.",
        "Fixe assento, coluna e pad de peito; solde os apoios de pés inclinados.",
        "Instale os eixos de pivô no cabeçote e chavete as cames sintetizadas.",
        "Monte as manivelas (braço + chifre) nos eixos; fixe as pegas.",
        "Enfie as anilhas nos chifres inclinados e faça o teste de carga.",
        "Posição de uso: sente atrás, peito no pad, pés nos apoios, puxe as pegas.",
    ]
    col_w = (doc.W - 2 * doc.m - 16) / 2
    img_h = 150.0
    for i in range(0, len(ETAPAS_MONTAGEM), 2):
        doc.precisa(img_h + 58)
        y_topo = doc.y
        for j in (0, 1):
            k = i + j
            if k >= len(ETAPAS_MONTAGEM):
                break
            x = doc.m + j * (col_w + 16)
            svg = renderizar_svg_3d(modelo, largura_px=640, yaw_graus=55, pitch_graus=12, etapa_max=k + 1)
            from reportlab.lib.utils import ImageReader

            doc.c.drawImage(ImageReader(_png_do_svg(svg, 760)), x, y_topo - img_h,
                            width=col_w, height=img_h, preserveAspectRatio=True, anchor="n")
            doc.c.setStrokeColor(_cor(_LINHA))
            doc.c.rect(x, y_topo - img_h, col_w, img_h, stroke=1, fill=0)
            doc.c.setFillColor(_cor(_ACC))
            doc.c.circle(x + 12, y_topo - img_h - 12, 8, stroke=0, fill=1)
            doc.c.setFillColor(_cor("#ffffff"))
            doc.c.setFont("Helvetica-Bold", 9)
            doc.c.drawCentredString(x + 12, y_topo - img_h - 15, str(k + 1))
            doc.c.setFillColor(_cor(_INK))
            doc.c.setFont("Helvetica-Bold", 9.5)
            doc.c.drawString(x + 26, y_topo - img_h - 16, ETAPAS_MONTAGEM[k])
            doc.c.setFillColor(_cor(_MUT))
            doc.c.setFont("Helvetica", 8)
            # instrução em até 2 linhas
            from reportlab.pdfbase.pdfmetrics import stringWidth

            palavras, l1, l2 = inst[k].split(), "", ""
            for p in palavras:
                if stringWidth((l1 + " " + p).strip(), "Helvetica", 8) <= col_w - 8:
                    l1 = (l1 + " " + p).strip()
                else:
                    l2 = (l2 + " " + p).strip()
            doc.c.drawString(x, y_topo - img_h - 30, l1)
            if l2:
                doc.c.drawString(x, y_topo - img_h - 40, l2)
        doc.y = y_topo - img_h - 52

    # Vista explodida
    doc.precisa(240)
    doc.paragrafo("Vista explodida (todas as etapas):", cor=_INK)
    svg_exp = renderizar_svg_3d(modelo, largura_px=1000, yaw_graus=55, pitch_graus=16, explosao=0.85)
    doc.imagem(_png_do_svg(svg_exp, 1200), doc.W - 2 * doc.m - 40, 300, borda=True)

    doc._rodape()
    doc.c.save()
    return caminho_pdf
