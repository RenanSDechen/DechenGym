"""
Testes do módulo de Geração de Imagem — estrutura BDD (Given/When/Then).
"""

import xml.etree.ElementTree as ET

import pytest

from dechengym.geracao_imagem import (
    gerar_preview_svg,
    montar_prompt_imagem_produto,
    renderizar_openscad_png,
)


class TestPreviewSVG:
    def test_gera_svg_valido(self):
        # Given parâmetros de geometria de uma máquina
        parametros = {
            "nome": "rosca_biceps",
            "altura_coluna_mm": 900,
            "comprimento_alavanca_mm": 350,
        }
        # When geramos o preview SVG
        svg = gerar_preview_svg(parametros)

        # Then é um documento SVG bem-formado (parseável como XML)
        raiz = ET.fromstring(svg)
        assert raiz.tag.endswith("svg")
        # And contém os elementos estruturais e o arco de movimento
        assert "<polyline" in svg  # arco de ADM
        assert "<circle" in svg    # pivô / pega
        assert "rosca_biceps" in svg

    def test_dimensoes_maiores_geram_svg_maior(self):
        # Given a mesma máquina em duas larguras
        p = {"altura_coluna_mm": 900, "comprimento_alavanca_mm": 350}
        # When geramos em 400 e 800 px
        svg_peq = gerar_preview_svg(p, largura_px=400)
        svg_gde = gerar_preview_svg(p, largura_px=800)
        # Then a largura declarada acompanha o parâmetro
        assert 'width="400"' in svg_peq
        assert 'width="800"' in svg_gde

    def test_arco_reflete_amplitude_informada(self):
        # Given ângulos inicial e final da ADM
        p = {"altura_coluna_mm": 900, "comprimento_alavanca_mm": 350}
        # When geramos com uma amplitude específica
        svg = gerar_preview_svg(p, angulo_inicial_graus=0, angulo_final_graus=90)
        # Then a legenda registra a amplitude
        assert "0-90 graus" in svg


class TestPromptImagemProduto:
    def test_prompt_pt_descreve_maquina(self):
        # Given parâmetros de geometria
        p = {"altura_coluna_mm": 1000, "comprimento_alavanca_mm": 800}
        # When montamos o prompt em português
        res = montar_prompt_imagem_produto(p, idioma="pt")
        # Then o prompt cita metalon e as dimensões, e há prompt negativo
        assert "metalon" in res["prompt"].lower()
        assert "1000" in res["prompt"]
        assert res["prompt_negativo"]

    def test_prompt_incorpora_ergonomia(self):
        # Given um envelope ergonômico com pegada supinada
        envelope = {
            "nome": "Rosca de biceps",
            "pegada": {"orientacao": {"orientacao": "supinada"}},
        }
        # When montamos o prompt
        res = montar_prompt_imagem_produto({}, envelope_ergonomico=envelope)
        # Then o prompt cita o exercício e a pegada
        assert "Rosca de biceps" in res["prompt"]
        assert "supinada" in res["prompt"]

    def test_prompt_en_muda_idioma(self):
        # Given o idioma inglês
        # When montamos o prompt
        res = montar_prompt_imagem_produto({}, idioma="en")
        # Then usa termos em inglês
        assert "Photorealistic" in res["prompt"]


class TestRenderOpenscadPng:
    def test_scad_inexistente_levanta_filenotfound(self, tmp_path):
        # Given um caminho de .scad que não existe
        inexistente = tmp_path / "nao_existe.scad"
        # When tentamos renderizar
        # Then levanta FileNotFoundError
        with pytest.raises(FileNotFoundError):
            renderizar_openscad_png(inexistente)

    def test_openscad_ausente_levanta_runtimeerror(self, tmp_path):
        # Given um .scad válido, mas um binário de OpenSCAD inexistente
        scad = tmp_path / "peca.scad"
        scad.write_text("cube([10,10,10]);", encoding="utf-8")
        # When tentamos renderizar com um binário que não existe
        # Then levanta RuntimeError com orientação
        with pytest.raises(RuntimeError):
            renderizar_openscad_png(scad, openscad_bin="openscad_inexistente_xyz")
